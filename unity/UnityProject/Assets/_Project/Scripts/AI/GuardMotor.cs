using UnityEngine;
using UnityEngine.AI;

namespace Lab01.AI
{
    [RequireComponent(typeof(NavMeshAgent), typeof(Perception))]
    public class GuardMotor : MonoBehaviour
    {
        [SerializeField] private Transform[] waypoints;
        [SerializeField] private float attackRange = 1.5f;
        [SerializeField] private float attackCooldown = 1f;
        [SerializeField] private float searchRadius = 2f;

        private NavMeshAgent agent;
        private int waypointIndex;
        private int searchIndex;
        private float nextAttackTime;
        private Vector3 lastKnownPosition;

        public Perception Senses { get; private set; }
        public bool CanAttack => Senses.Player != null && Senses.CanSeePlayer &&
            Vector3.Distance(new Vector3(transform.position.x, 0, transform.position.z),
                new Vector3(Senses.Player.position.x, 0, Senses.Player.position.z)) <= attackRange;
        public Vector3 LastKnownPosition => lastKnownPosition;

        private void Awake()
        {
            agent = GetComponent<NavMeshAgent>();
            Senses = GetComponent<Perception>();
        }

        private void Start()
        {
            // В сцене агент выключен до загрузки NavMesh. Включаем его после OnEnable у NavMeshLoader.
            NavMeshHit hit;
            if (NavMesh.SamplePosition(transform.position, out hit, 2f, NavMesh.AllAreas))
            {
                transform.position = hit.position;
                agent.enabled = true;
            }
            else Debug.LogError("Не удалось найти NavMesh рядом со стражником.", this);
        }

        public void RememberPlayer()
        {
            if (Senses.Player != null) lastKnownPosition = Senses.Player.position;
        }

        public void Stop()
        {
            if (agent.isOnNavMesh) agent.isStopped = true;
        }

        public void Patrol()
        {
            if (!agent.isOnNavMesh || waypoints.Length == 0) return;
            agent.isStopped = false;
            if (agent.pathPending || (agent.hasPath && agent.remainingDistance > 0.5f)) return;
            agent.SetDestination(waypoints[waypointIndex].position);
            waypointIndex = (waypointIndex + 1) % waypoints.Length;
        }

        public void Chase()
        {
            if (!agent.isOnNavMesh || Senses.Player == null) return;
            agent.isStopped = false;
            agent.SetDestination(Senses.Player.position);
        }

        public void BeginSearch()
        {
            searchIndex = 0;
            if (agent.isOnNavMesh) agent.ResetPath();
        }

        public void Search()
        {
            if (!agent.isOnNavMesh) return;
            agent.isStopped = false;
            if (agent.pathPending || (agent.hasPath && agent.remainingDistance > 0.5f)) return;

            // Сначала последняя известная точка, затем четыре точки вокруг неё.
            Vector3 offset = searchIndex == 0 ? Vector3.zero :
                Quaternion.Euler(0, (searchIndex - 1) * 90f, 0) * Vector3.forward * searchRadius;
            searchIndex = (searchIndex + 1) % 5;
            NavMeshHit hit;
            if (NavMesh.SamplePosition(lastKnownPosition + offset, out hit, 2f, NavMesh.AllAreas))
                agent.SetDestination(hit.position);
        }

        public void Attack()
        {
            Stop();
            if (Time.time < nextAttackTime) return;
            nextAttackTime = Time.time + attackCooldown;
            Debug.Log("Стражник атакует игрока (демонстрационная атака).", this);
        }
    }
}
