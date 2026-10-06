using Lab01.AI;
using UnityEngine;
using UnityEngine.AI;

namespace Lab02.Telemetry
{
    // Небольшой игровой сценарий: контрольная точка, выход и смерть от трёх ударов.
    [RequireComponent(typeof(TelemetryLogger))]
    public class TelemetryGame : MonoBehaviour
    {
        [SerializeField] private Transform player;
        [SerializeField] private GuardMotor guard;
        [SerializeField] private Transform checkpoint;
        [SerializeField] private Transform exit;
        private TelemetryLogger logger;
        private Vector3 spawn;
        private Vector3 guardSpawn;
        private float startedAt;
        private int health;
        private bool checkpointReached;
        private bool active;
        private string level = "L1";
        private string message = "Доберитесь до зелёной точки, затем до жёлтого выхода.";
        public bool CheckpointReached => checkpointReached;
        public bool Active => active;
        public int Health => health;

        private void Start()
        {
            logger = GetComponent<TelemetryLogger>();
            spawn = player.position;
            guardSpawn = guard.transform.position;
            guard.Attacked += OnHit;
            BeginRound("L1");
        }

        public void BeginRound(string selectedLevel)
        {
            level = selectedLevel;
            checkpointReached = false;
            health = 3;
            active = true;
            startedAt = Time.time;
            MovePlayer(spawn);
            // Оба уровня используют одну комнату: L1 — FSM, L2 — BT и более быстрый стражник.
            guard.GetComponent<GuardMode>().SetAlgorithm(level == "L1"
                ? GuardMode.Algorithm.FSM : GuardMode.Algorithm.BehaviorTree);
            NavMeshAgent agent = guard.GetComponent<NavMeshAgent>();
            if (agent.isOnNavMesh) agent.Warp(guardSpawn);
            agent.speed = level == "L1" ? 3.5f : 4.2f;
            logger.BeginSession(level);
            message = "Доберитесь до зелёной точки, затем до жёлтого выхода.";
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.R)) BeginRound(level);
            if (Input.GetKeyDown(KeyCode.Alpha1)) BeginRound("L1");
            if (Input.GetKeyDown(KeyCode.Alpha2)) BeginRound("L2");
            if (!active) return;
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                logger.EndSession("quit");
                active = false;
                message = "Сессия завершена. R — начать снова.";
                return;
            }
            if (!checkpointReached && Near(checkpoint))
            {
                checkpointReached = true;
                logger.Log("checkpoint", player.position);
                message = "Контрольная точка достигнута. Теперь идите к жёлтому выходу.";
            }
            if (checkpointReached && Near(exit))
            {
                logger.Log("level_complete", player.position,
                    new TelemetryLogger.Payload { time_s = Time.time - startedAt });
                logger.EndSession("complete");
                active = false;
                message = "Уровень пройден! R — повторить; 1/2 — выбрать уровень.";
            }
        }

        private bool Near(Transform marker)
        {
            Vector3 difference = player.position - marker.position;
            difference.y = 0;
            return difference.magnitude <= 1.4f;
        }

        private void OnHit()
        {
            if (!active) return;
            health--;
            if (health > 0) return;
            // Записываем место смерти до перемещения к точке возрождения.
            logger.Log("death", player.position, new TelemetryLogger.Payload { cause = "guard" });
            MovePlayer(checkpointReached ? checkpoint.position + Vector3.up : spawn);
            health = 3;
            message = "Стражник поймал игрока. Возрождение; прогресс контрольной точки сохранён.";
        }

        private void MovePlayer(Vector3 position)
        {
            CharacterController controller = player.GetComponent<CharacterController>();
            controller.enabled = false; // Телепортация не должна столкнуться с прежним положением капсулы.
            player.position = position;
            controller.enabled = true;
        }

        private void OnGUI()
        {
            GUIStyle text = new GUIStyle(GUI.skin.label) { fontSize = 17, wordWrap = true };
            GUI.Box(new Rect(12, 12, 610, 138), "");
            GUI.Label(new Rect(24, 20, 585, 28), "ЛР 2 · " + level + " · Здоровье: " + health + "/3", text);
            GUI.Label(new Rect(24, 48, 585, 50), message, text);
            GUI.Label(new Rect(24, 106, 585, 30), "WASD — движение · R — заново · 1/2 — уровень · Esc — конец", text);
        }

        private void OnDestroy()
        {
            if (guard != null) guard.Attacked -= OnHit;
        }
    }
}
