using UnityEngine;

namespace Lab01.AI
{
    [RequireComponent(typeof(GuardMotor))]
    public class GuardFSM : MonoBehaviour
    {
        [SerializeField] private float alertDuration = 1f;
        [SerializeField] private float lostTargetDelay = 2f;
        [SerializeField] private float searchDuration = 10f;

        private GuardMotor motor;
        private float stateTime;
        private float unseenTime;
        public GuardState State { get; private set; } = GuardState.Patrol;

        private void Awake() => motor = GetComponent<GuardMotor>();

        private void OnEnable()
        {
            State = GuardState.Patrol;
            stateTime = unseenTime = 0f;
        }

        private void Update()
        {
            stateTime += Time.deltaTime;
            bool seesPlayer = motor.Senses.CanSeePlayer;
            if (seesPlayer) motor.RememberPlayer();

            switch (State)
            {
                case GuardState.Patrol:
                    if (seesPlayer) ChangeState(GuardState.Alert);
                    else motor.Patrol();
                    break;
                case GuardState.Alert:
                    motor.Stop();
                    if (!seesPlayer) ChangeState(GuardState.Patrol);
                    else if (stateTime >= alertDuration) ChangeState(GuardState.Chase);
                    break;
                case GuardState.Chase:
                    if (motor.CanAttack) ChangeState(GuardState.Attack);
                    else if (LostTarget(seesPlayer)) ChangeState(GuardState.Search);
                    else if (seesPlayer) motor.Chase();
                    else motor.Search(); // Идём к последней известной точке.
                    break;
                case GuardState.Attack:
                    if (!motor.CanAttack) ChangeState(GuardState.Chase);
                    else motor.Attack();
                    break;
                case GuardState.Search:
                    if (seesPlayer) ChangeState(GuardState.Alert);
                    else if (stateTime >= searchDuration) ChangeState(GuardState.Patrol);
                    else motor.Search();
                    break;
            }
        }

        private bool LostTarget(bool seesPlayer)
        {
            unseenTime = seesPlayer ? 0f : unseenTime + Time.deltaTime;
            return unseenTime >= lostTargetDelay;
        }

        private void ChangeState(GuardState next)
        {
            if (State == next) return;
            Debug.Log($"[FSM] {State} -> {next}", this);
            State = next;
            stateTime = 0f;
            if (next == GuardState.Chase) unseenTime = 0f;
            if (next == GuardState.Search) motor.BeginSearch();
            if (next == GuardState.Patrol) motor.Stop();
        }
    }
}
