using Lab01.AI;
using UnityEngine;

namespace Lab01.BT
{
    // То же поведение стражника, но выбор действия делает дерево приоритетов.
    [RequireComponent(typeof(GuardMotor))]
    public class GuardBT : MonoBehaviour
    {
        [SerializeField] private float alertDuration = 1f;
        [SerializeField] private float lostTargetDelay = 2f;
        [SerializeField] private float searchDuration = 10f;

        private GuardMotor motor;
        private Node root;
        private float alertUntil;
        private float lastSeenTime;
        private float searchUntil;
        private GuardState state;
        public GuardState State => state;

        private void Awake()
        {
            motor = GetComponent<GuardMotor>();
            // Selector берёт первую ветку, которая не вернула Failure.
            // Поэтому порядок здесь задаёт приоритет: атака, тревога, погоня, поиск, патруль.
            root = new Selector(
                new Sequence(new Condition(() => motor.CanAttack && (state == GuardState.Chase || state == GuardState.Attack)), new Action(Attack)),
                new Sequence(new Condition(() => motor.Senses.CanSeePlayer && state == GuardState.Alert), new Action(Alert)),
                new Sequence(new Condition(() => motor.Senses.CanSeePlayer), new Action(SeePlayer)),
                new Sequence(new Condition(() => (state == GuardState.Chase || state == GuardState.Attack) && Time.time - lastSeenTime < lostTargetDelay), new Action(GoToLastPosition)),
                new Sequence(new Condition(() => state == GuardState.Chase || state == GuardState.Attack || state == GuardState.Search), new Action(Search)),
                new Action(Patrol));
        }

        private void OnEnable()
        {
            state = GuardState.Patrol;
            lastSeenTime = -1000f;
        }

        private void Update()
        {
            // Запоминаем цель до обхода дерева, чтобы поиск знал, куда идти.
            if (motor.Senses.CanSeePlayer)
            {
                lastSeenTime = Time.time;
                motor.RememberPlayer();
            }
            root.Tick();
        }

        private Status SeePlayer()
        {
            // При первом обнаружении ждём секунду; во время погони задержка не нужна.
            if (state != GuardState.Chase && state != GuardState.Attack)
            {
                SetState(GuardState.Alert);
                alertUntil = Time.time + alertDuration;
                motor.Stop();
            }
            else
            {
                SetState(GuardState.Chase);
                motor.Chase();
            }
            return Status.Running;
        }

        private Status Alert()
        {
            if (Time.time >= alertUntil)
            {
                SetState(GuardState.Chase);
                motor.Chase();
            }
            else motor.Stop();
            return Status.Running;
        }

        private Status Attack()
        {
            SetState(GuardState.Attack);
            motor.Attack();
            return Status.Running;
        }

        private Status GoToLastPosition()
        {
            // Двухсекундный таймер проверяется условием ветви в Awake().
            motor.Search();
            return Status.Running;
        }

        private Status Search()
        {
            // Время поиска отсчитывается только после перехода в Search.
            if (state != GuardState.Search)
            {
                SetState(GuardState.Search);
                searchUntil = Time.time + searchDuration;
                motor.BeginSearch();
            }
            if (Time.time >= searchUntil) return Status.Failure;
            motor.Search();
            return Status.Running;
        }

        private Status Patrol()
        {
            SetState(GuardState.Patrol);
            motor.Patrol();
            return Status.Running;
        }

        private void SetState(GuardState next)
        {
            if (state == next) return;
            Debug.Log($"[BT] {state} -> {next}", this);
            state = next;
        }
    }
}
