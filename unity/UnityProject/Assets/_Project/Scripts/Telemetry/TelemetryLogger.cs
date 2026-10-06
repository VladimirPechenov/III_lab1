using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace Lab02.Telemetry
{
    // Каждое событие сразу записывается в JSONL, затем отправляется на сервер пакетом.
    public class TelemetryLogger : MonoBehaviour
    {
        [Serializable]
        public class Payload
        {
            public string cause;
            public string reason;
            public float time_s;
        }

        [Serializable]
        public class Event
        {
            public int schema_version = 1;
            public string event_id, session_id, player_id, event_type, level;
            public string source = "unity";
            public double ts;
            public float x, y;
            public Payload payload = new Payload();
        }

        [SerializeField] private string serverUrl = "http://127.0.0.1:8000/events";
        [SerializeField] private bool sendHttp = true;
        [SerializeField] private float flushInterval = 2f;
        [SerializeField] private string playerId = "player-01";

        private readonly List<Event> pending = new List<Event>();
        private string sessionId;
        private string level;
        private bool sending;
        private bool warned;
        private float nextFlush;
        public bool SessionOpen { get; private set; }
        public string FilePath { get; private set; }
        public int PendingCount => pending.Count;

        private void Awake()
        {
            // В редакторе файл лежит рядом с Python-частью проекта; в сборке — в persistentDataPath.
            string folder = Application.isEditor
                ? Path.GetFullPath(Path.Combine(Application.dataPath, "../../../data"))
                : Application.persistentDataPath;
            Directory.CreateDirectory(folder);
            FilePath = Path.Combine(folder, "unity-events.jsonl");
        }

        public void BeginSession(string selectedLevel)
        {
            if (SessionOpen) EndSession("restart");
            sessionId = Guid.NewGuid().ToString("N");
            level = selectedLevel;
            SessionOpen = true;
            Log("session_start", Vector3.zero);
        }

        public void Log(string type, Vector3 position, Payload payload = null)
        {
            if (!SessionOpen) return;
            Event item = new Event
            {
                event_id = Guid.NewGuid().ToString("N"), session_id = sessionId,
                player_id = playerId, event_type = type, level = level,
                ts = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0,
                x = position.x, y = position.z, payload = payload ?? new Payload()
            };
            // Для карты комнаты берём X/Z Unity и сохраняем их в поля x/y схемы события.
            File.AppendAllText(FilePath, JsonUtility.ToJson(item) + "\n", new UTF8Encoding(false));
            pending.Add(item);
        }

        public void EndSession(string reason)
        {
            if (!SessionOpen) return;
            Log("session_end", Vector3.zero, new Payload { reason = reason });
            SessionOpen = false;
        }

        private void Update()
        {
            if (Time.unscaledTime < nextFlush) return;
            nextFlush = Time.unscaledTime + flushInterval;
            if (sendHttp && !sending && pending.Count > 0) StartCoroutine(Post());
        }

        private IEnumerator Post()
        {
            sending = true;
            int count = Math.Min(pending.Count, 100);
            List<Event> batch = pending.GetRange(0, count);
            string json = "[" + string.Join(",", batch.ConvertAll(item => JsonUtility.ToJson(item))) + "]";
            using (UnityWebRequest request = new UnityWebRequest(serverUrl, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                request.downloadHandler = new DownloadHandlerBuffer();
                request.timeout = 5;
                request.SetRequestHeader("Content-Type", "application/json");
                yield return request.SendWebRequest();
                if (request.result == UnityWebRequest.Result.Success)
                {
                    // Пока шёл запрос, могли появиться новые события. Удаляем только отправленный пакет.
                    pending.RemoveRange(0, count);
                    warned = false;
                }
                else if (!warned)
                {
                    Debug.LogWarning("Телеметрия сохранена в JSONL; сервер пока недоступен: " + request.error, this);
                    warned = true;
                }
            }
            sending = false;
        }

        private void OnApplicationQuit() => EndSession("quit");
        private void OnDisable() => EndSession("stop");
        // При закрытии игры корутины не успевают отправить пакет. JSONL можно импортировать позже.
    }
}
