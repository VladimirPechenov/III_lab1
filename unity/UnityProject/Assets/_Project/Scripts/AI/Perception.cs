using UnityEngine;

namespace Lab01.AI
{
    // Проверяет угол обзора, дальность и отсутствие стены между стражником и игроком.
    public class Perception : MonoBehaviour
    {
        [SerializeField] private Transform player;
        [SerializeField] private float viewDistance = 10f;
        [SerializeField, Range(1f, 180f)] private float fieldOfView = 90f;
        [SerializeField] private LayerMask obstacles = ~0;

        public Transform Player => player;
        public bool CanSeePlayer { get; private set; }

        private void Update()
        {
            CanSeePlayer = false;
            if (player == null) return;

            Vector3 eye = transform.position + Vector3.up * 1.5f;
            Vector3 target = player.position + Vector3.up;
            Vector3 direction = target - eye;
            if (direction.magnitude > viewDistance) return;
            if (Vector3.Angle(transform.forward, direction) > fieldOfView * 0.5f) return;

            // Маска содержит только препятствия. Коллайдер игрока не закрывает луч.
            CanSeePlayer = !Physics.Raycast(eye, direction.normalized, direction.magnitude, obstacles);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = CanSeePlayer ? Color.red : Color.yellow;
            Vector3 eye = transform.position + Vector3.up * 1.5f;
            Gizmos.DrawRay(eye, Quaternion.Euler(0, -fieldOfView / 2f, 0) * transform.forward * viewDistance);
            Gizmos.DrawRay(eye, Quaternion.Euler(0, fieldOfView / 2f, 0) * transform.forward * viewDistance);
        }
    }
}
