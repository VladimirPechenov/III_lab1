using UnityEngine;
using UnityEngine.AI;

namespace Lab01.AI
{
    // Держит запечённую навигацию в сцене при запуске игры.
    public class NavMeshLoader : MonoBehaviour
    {
        [SerializeField] private NavMeshData data;
        private NavMeshDataInstance instance;

        private void OnEnable()
        {
            if (data != null) instance = NavMesh.AddNavMeshData(data);
        }

        private void OnDisable()
        {
            if (instance.valid) instance.Remove();
        }
    }
}
