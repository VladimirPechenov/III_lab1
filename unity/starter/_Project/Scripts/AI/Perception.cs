using UnityEngine;

namespace Lab01.AI
{
    /// <summary>Сенсоры: конус зрения (FOV + raycast) и слух (радиус).</summary>
    public class Perception : MonoBehaviour
    {
        [SerializeField] private Transform player;
        [SerializeField] private float viewDistance = 10f;
        [SerializeField, Range(0, 180)] private float fov = 90f;
        [SerializeField] private float hearingRadius = 6f;
        [SerializeField] private LayerMask obstacles;

        public bool CanSeePlayer { get; private set; }
        public bool HeardNoise { get; set; }

        private void Update()
        {
            var to = player.position - transform.position;
            CanSeePlayer = to.magnitude <= viewDistance
                && Vector3.Angle(transform.forward, to) <= fov / 2f
                && !Physics.Raycast(transform.position + Vector3.up, to.normalized, to.magnitude, obstacles);
        }

        public void OnNoise(Vector3 at) => HeardNoise = Vector3.Distance(transform.position, at) <= hearingRadius;

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.yellow; Gizmos.DrawWireSphere(transform.position, hearingRadius);
            Gizmos.color = CanSeePlayer ? Color.red : Color.green; Gizmos.DrawRay(transform.position, transform.forward * viewDistance);
        }
    }
}
