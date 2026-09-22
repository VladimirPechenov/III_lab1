using System.Collections.Generic;
using Lab01.AI;
using Lab01.BT;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;

public static class CreateLabScene
{
    [MenuItem("Lab 01/Create demonstration scene")]
    public static void Create()
    {
        // Сцену можно получить из одного пункта меню без ручной расстановки объектов.
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        GameObject environment = new GameObject("Environment");
        Material floor = MakeMaterial("Floor", new Color(0.25f, 0.35f, 0.38f));
        Material wall = MakeMaterial("Walls", new Color(0.2f, 0.25f, 0.33f));
        Material obstacle = MakeMaterial("Obstacles", new Color(0.55f, 0.34f, 0.25f));
        Material blue = MakeMaterial("Player", new Color(0.15f, 0.55f, 0.95f));
        Material red = MakeMaterial("Guard", new Color(0.85f, 0.22f, 0.18f));

        Block("Floor", new Vector3(0, -0.25f, 0), new Vector3(20, 0.5f, 20), floor, environment.transform);
        Block("Wall North", new Vector3(0, 1, 10), new Vector3(20, 2, 0.5f), wall, environment.transform);
        Block("Wall South", new Vector3(0, 1, -10), new Vector3(20, 2, 0.5f), wall, environment.transform);
        Block("Wall East", new Vector3(10, 1, 0), new Vector3(0.5f, 2, 20), wall, environment.transform);
        Block("Wall West", new Vector3(-10, 1, 0), new Vector3(0.5f, 2, 20), wall, environment.transform);
        Block("Obstacle 1", new Vector3(-3, 1, 0), new Vector3(2, 2, 2), obstacle, environment.transform);
        Block("Obstacle 2", new Vector3(3, 1, 0), new Vector3(2, 2, 2), obstacle, environment.transform);
        Block("Obstacle 3", new Vector3(0, 1, -3), new Vector3(2, 2, 2), obstacle, environment.transform);
        Block("Obstacle 4", new Vector3(0, 1, 3), new Vector3(2, 2, 2), obstacle, environment.transform);

        Vector3[] points = { new Vector3(-7, 0, -7), new Vector3(-7, 0, 7),
            new Vector3(7, 0, 7), new Vector3(7, 0, -7) };
        Transform[] waypoints = new Transform[points.Length];
        // Порядок точек образует замкнутый маршрут вокруг центра комнаты.
        for (int i = 0; i < points.Length; i++)
        {
            GameObject point = new GameObject("Waypoint " + (i + 1));
            point.transform.position = points[i];
            waypoints[i] = point.transform;
        }

        GameObject player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        player.name = "Player (WASD)";
        player.layer = 2; // Ignore Raycast
        player.transform.position = new Vector3(6, 1, 0);
        Object.DestroyImmediate(player.GetComponent<CapsuleCollider>());
        player.AddComponent<CharacterController>();
        player.AddComponent<PlayerController>();
        player.GetComponent<Renderer>().sharedMaterial = blue;

        GameObject guard = new GameObject();
        guard.name = "Guard (select FSM or BT here)";
        guard.layer = 2;
        // У визуальной капсулы нет коллайдера: движение и обход выполняет NavMeshAgent.
        guard.transform.position = points[0];
        GameObject guardVisual = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        guardVisual.name = "Guard visual";
        guardVisual.layer = 2;
        guardVisual.transform.SetParent(guard.transform);
        guardVisual.transform.localPosition = Vector3.up;
        Object.DestroyImmediate(guardVisual.GetComponent<CapsuleCollider>());
        guardVisual.GetComponent<Renderer>().sharedMaterial = red;
        var agent = guard.AddComponent<NavMeshAgent>();
        agent.speed = 3.5f;
        agent.angularSpeed = 300f;
        agent.stoppingDistance = 0.3f;
        agent.enabled = false; // GuardMotor включит агент после загрузки NavMesh.
        var senses = guard.AddComponent<Perception>();
        var motor = guard.AddComponent<GuardMotor>();
        var fsm = guard.AddComponent<GuardFSM>();
        var bt = guard.AddComponent<GuardBT>();
        var mode = guard.AddComponent<GuardMode>();
        SetObject(senses, "player", player.transform);
        // Луч зрения должен сталкиваться с геометрией, но не с самим игроком и стражником.
        SetInt(senses, "obstacles", 1 << 0); // Default: комната и четыре препятствия.
        SetArray(motor, "waypoints", waypoints);
        SetObject(mode, "fsm", fsm);
        SetObject(mode, "behaviorTree", bt);
        bt.enabled = false;

        // Навигация строится только из геометрии комнаты.
        var sources = new List<NavMeshBuildSource>();
        NavMeshBuilder.CollectSources(environment.transform, ~0, NavMeshCollectGeometry.PhysicsColliders,
            0, new List<NavMeshBuildMarkup>(), sources);
        Bounds bounds = new Bounds(Vector3.zero, new Vector3(24, 6, 24));
        NavMeshData navData = NavMeshBuilder.BuildNavMeshData(
            NavMesh.GetSettingsByID(agent.agentTypeID), sources, bounds, Vector3.zero, Quaternion.identity);
        System.IO.Directory.CreateDirectory("Assets/_Project/Navigation");
        AssetDatabase.CreateAsset(navData, "Assets/_Project/Navigation/GuardNavMesh.asset");
        var loader = environment.AddComponent<NavMeshLoader>();
        // Loader возвращает запечённые данные в NavMesh при входе в Play Mode.
        SetObject(loader, "data", navData);

        GameObject cameraObject = new GameObject("Main Camera");
        cameraObject.tag = "MainCamera";
        cameraObject.transform.position = new Vector3(0, 22, -16);
        cameraObject.transform.LookAt(Vector3.zero);
        var camera = cameraObject.AddComponent<Camera>();
        camera.fieldOfView = 55f;
        cameraObject.AddComponent<AudioListener>();
        GameObject lightObject = new GameObject("Directional Light");
        lightObject.transform.rotation = Quaternion.Euler(50, -30, 0);
        lightObject.AddComponent<Light>().type = LightType.Directional;

        System.IO.Directory.CreateDirectory("Assets/_Project/Scenes");
        string scenePath = "Assets/_Project/Scenes/Lab01.unity";
        EditorSceneManager.SaveScene(scene, scenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(scenePath, true) };
        AssetDatabase.SaveAssets();
        Debug.Log("Lab01 scene created: " + scenePath + ", navigation sources: " + sources.Count);
    }

    private static GameObject Block(string name, Vector3 position, Vector3 scale, Material material, Transform parent)
    {
        var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
        block.name = name;
        block.transform.SetParent(parent);
        block.transform.position = position;
        block.transform.localScale = scale;
        block.GetComponent<Renderer>().sharedMaterial = material;
        return block;
    }

    private static Material MakeMaterial(string name, Color color)
    {
        System.IO.Directory.CreateDirectory("Assets/_Project/Materials");
        var material = new Material(Shader.Find("Standard"));
        material.color = color;
        AssetDatabase.CreateAsset(material, "Assets/_Project/Materials/" + name + ".mat");
        return material;
    }

    private static void SetObject(Object target, string field, Object value)
    {
        var serialized = new SerializedObject(target);
        serialized.FindProperty(field).objectReferenceValue = value;
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    private static void SetInt(Object target, string field, int value)
    {
        var serialized = new SerializedObject(target);
        serialized.FindProperty(field).intValue = value;
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    private static void SetArray(Object target, string field, Transform[] values)
    {
        // SerializedObject сохраняет ссылки на объекты сцены так же, как назначение в Inspector.
        var serialized = new SerializedObject(target);
        var array = serialized.FindProperty(field);
        array.arraySize = values.Length;
        for (int i = 0; i < values.Length; i++) array.GetArrayElementAtIndex(i).objectReferenceValue = values[i];
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }
}
