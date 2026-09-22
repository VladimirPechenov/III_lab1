using System.Collections.Generic;

namespace Lab01.BT
{
    // Running означает, что действие продолжится на следующем кадре.
    public enum Status { Success, Failure, Running }

    public abstract class Node
    {
        public abstract Status Tick();
    }

    public class Sequence : Node
    {
        private readonly List<Node> children;

        public Sequence(params Node[] children) => this.children = new List<Node>(children);

        public override Status Tick()
        {
            // Последовательность успешна, только если успешны все её дети.
            foreach (Node child in children)
            {
                Status result = child.Tick();
                if (result != Status.Success) return result;
            }

            return Status.Success;
        }
    }

    public class Selector : Node
    {
        private readonly List<Node> children;

        public Selector(params Node[] children) => this.children = new List<Node>(children);

        public override Status Tick()
        {
            // Проверяем альтернативы слева направо до первой подходящей ветви.
            foreach (Node child in children)
            {
                Status result = child.Tick();
                if (result != Status.Failure) return result;
            }

            return Status.Failure;
        }
    }

    public class Condition : Node
    {
        private readonly System.Func<bool> check;

        public Condition(System.Func<bool> check) => this.check = check;

        public override Status Tick() => check() ? Status.Success : Status.Failure;
    }

    public class Action : Node
    {
        private readonly System.Func<Status> run;

        public Action(System.Func<Status> run) => this.run = run;

        public override Status Tick() => run();
    }
}
