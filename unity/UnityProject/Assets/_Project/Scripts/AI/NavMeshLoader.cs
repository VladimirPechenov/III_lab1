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
            // Данные навигации лежат в отдельном asset и должны быть добавлены в мир при запуске.
            if (data != null) instance = NavMesh.AddNavMeshData(data);
        }

        private void OnDisable()
        {
            // Убираем только экземпляр, который добавил этот компонент.
            if (instance.valid) instance.Remove();
        }
    }
}
