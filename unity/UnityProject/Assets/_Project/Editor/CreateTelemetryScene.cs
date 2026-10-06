using Lab01.AI;
using Lab02.Telemetry;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class CreateTelemetryScene
{
    [MenuItem("Lab 02/Create telemetry scene")]
    public static void Create()
    {
        // Комната и навигация берутся из готовой сцены первой работы.
        var scene = EditorSceneManager.OpenScene("Assets/_Project/Scenes/Lab01.unity");
        var player = GameObject.Find("Player (WASD)").transform;
        var guard = GameObject.Find("Guard (select FSM or BT here)").GetComponent<GuardMotor>();
        var checkpoint = Marker("Checkpoint", new Vector3(-6, 0.06f, 5), new Color(0.15f, 0.8f, 0.4f));
        var exit = Marker("Exit", new Vector3(6, 0.06f, 7), new Color(1f, 0.8f, 0.15f));
        var telemetry = new GameObject("Telemetry");
        telemetry.AddComponent<TelemetryLogger>();
        var game = telemetry.AddComponent<TelemetryGame>();
        var serialized = new SerializedObject(game);
        serialized.FindProperty("player").objectReferenceValue = player;
        serialized.FindProperty("guard").objectReferenceValue = guard;
        serialized.FindProperty("checkpoint").objectReferenceValue = checkpoint;
        serialized.FindProperty("exit").objectReferenceValue = exit;
        serialized.ApplyModifiedPropertiesWithoutUndo();
        string path = "Assets/_Project/Scenes/Lab02.unity";
        EditorSceneManager.SaveScene(scene, path);
        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene(path, true),
            new EditorBuildSettingsScene("Assets/_Project/Scenes/Lab01.unity", true)
        };
        AssetDatabase.SaveAssets();
        Debug.Log("Сцена телеметрии сохранена: " + path);
    }

    private static Transform Marker(string name, Vector3 position, Color color)
    {
        var marker = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        marker.name = name;
        marker.transform.position = position;
        marker.transform.localScale = new Vector3(2.2f, 0.04f, 2.2f);
        Object.DestroyImmediate(marker.GetComponent<Collider>());
        // Повторный вызов меню использует уже сохранённый материал.
        string path = "Assets/_Project/Materials/" + name + ".mat";
        Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Standard"));
            material.color = color;
            AssetDatabase.CreateAsset(material, path);
        }
        marker.GetComponent<Renderer>().sharedMaterial = material;
        return marker.transform;
    }
}
