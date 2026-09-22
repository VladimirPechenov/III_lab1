using UnityEngine;
using UnityEngine.AI;

namespace Lab01.AI
{
    /// <summary>Вариант 1: FSM через switch. Заполните обработчики состояний.</summary>
    public class GuardFSM : MonoBehaviour
    {
        [SerializeField] private Transform[] waypoints;
        [SerializeField] private Perception perception;
        [SerializeField] private float alertTimeout = 3f;

        public GuardState State { get; private set; } = GuardState.Patrol;
        private NavMeshAgent _agent;
        private float _alertTimer;
        private int _wp;

        private void Awake() => _agent = GetComponent<NavMeshAgent>();

        private void Update()
        {
            switch (State)
            {
                case GuardState.Patrol: Patrol(); break;
                case GuardState.Alert: Alert(); break;
                case GuardState.Chase: Chase(); break;
                case GuardState.Attack: Attack(); break;
                case GuardState.Return: ReturnToPost(); break;
            }
        }

        private void Transition(GuardState next)
        {
            Debug.Log($"[FSM] {State} -> {next}");
            State = next;
        }

        private void Patrol()
        {
            if (perception.CanSeePlayer || perception.HeardNoise) { _alertTimer = 0; Transition(GuardState.Alert); return; }
            if (waypoints.Length == 0) return;
            if (!_agent.hasPath || _agent.remainingDistance < 0.5f) _agent.SetDestination(waypoints[_wp++ % waypoints.Length].position);
        }

        private void Alert()
        {
            _alertTimer += Time.deltaTime;
            if (perception.CanSeePlayer) { Transition(GuardState.Chase); return; }
            if (_alertTimer > alertTimeout) Transition(GuardState.Patrol);
        }

        private void Chase() { /* TODO */ }
        private void Attack() { /* TODO */ }
        private void ReturnToPost() { /* TODO */ }
    }
}
