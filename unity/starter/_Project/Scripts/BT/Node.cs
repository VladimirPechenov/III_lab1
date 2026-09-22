using System.Collections.Generic;

namespace Lab01.BT
{
    public enum Status { Success, Failure, Running }

    public abstract class Node { public abstract Status Tick(); }

    public class Sequence : Node
    {
        private readonly List<Node> _children; public Sequence(params Node[] c) => _children = new(c);
        public override Status Tick() { foreach (var c in _children) { var s = c.Tick(); if (s != Status.Success) return s; } return Status.Success; }
    }

    public class Selector : Node
    {
        private readonly List<Node> _children; public Selector(params Node[] c) => _children = new(c);
        public override Status Tick() { foreach (var c in _children) { var s = c.Tick(); if (s != Status.Failure) return s; } return Status.Failure; }
    }

    public class Condition : Node
    {
        private readonly System.Func<bool> _f; public Condition(System.Func<bool> f) => _f = f;
        public override Status Tick() => _f() ? Status.Success : Status.Failure;
    }

    public class Action : Node
    {
        private readonly System.Func<Status> _f; public Action(System.Func<Status> f) => _f = f;
        public override Status Tick() => _f();
    }
}
