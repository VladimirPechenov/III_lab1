using UnityEngine;
using Lab01.AI;

namespace Lab01.BT
{
    /// <summary>Вариант 2: то же поведение стражника на дереве поведения.</summary>
    public class GuardBT : MonoBehaviour
    {
        [SerializeField] private Perception perception;
        private Node _root;

        private void Start()
        {
            _root = new Selector(
                new Sequence(new Condition(() => perception.CanSeePlayer), new Action(Chase)),
                new Sequence(new Condition(() => perception.HeardNoise), new Action(Investigate)),
                new Action(Patrol));
        }

        private void Update() => _root.Tick();

        private Status Chase() { /* TODO */ return Status.Running; }
        private Status Investigate() { /* TODO */ return Status.Running; }
        private Status Patrol() { /* TODO */ return Status.Running; }
    }
}
