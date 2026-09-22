using Lab01.BT;
using UnityEngine;

namespace Lab01.AI
{
    // Режим меняется в Inspector без замены сцены или объектов.
    public class GuardMode : MonoBehaviour
    {
        public enum Algorithm { FSM, BehaviorTree }
        [SerializeField] private Algorithm algorithm = Algorithm.FSM;
        [SerializeField] private GuardFSM fsm;
        [SerializeField] private GuardBT behaviorTree;

        private void OnValidate()
        {
            // Inspector вызывает OnValidate при смене режима. Awake повторяет выбор при запуске сцены.
            if (fsm == null) fsm = GetComponent<GuardFSM>();
            if (behaviorTree == null) behaviorTree = GetComponent<GuardBT>();
            if (fsm != null) fsm.enabled = algorithm == Algorithm.FSM;
            if (behaviorTree != null) behaviorTree.enabled = algorithm == Algorithm.BehaviorTree;
        }

        private void Awake() => OnValidate();
    }
}
