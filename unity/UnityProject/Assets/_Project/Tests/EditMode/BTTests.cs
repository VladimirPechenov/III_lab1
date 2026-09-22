using Lab01.BT;
using NUnit.Framework;

public class BTTests
{
    [Test]
    public void SelectorUsesNextChildAfterFailure()
    {
        // Первая ветвь не подошла, значит Selector должен выполнить вторую.
        var tree = new Selector(new Condition(() => false), new Lab01.BT.Action(() => Status.Running));
        Assert.AreEqual(Status.Running, tree.Tick());
    }

    [Test]
    public void SequenceStopsAfterFailure()
    {
        // После провала условия действие вызываться не должно.
        int calls = 0;
        var tree = new Sequence(new Condition(() => false),
            new Lab01.BT.Action(() => { calls++; return Status.Success; }));
        Assert.AreEqual(Status.Failure, tree.Tick());
        Assert.AreEqual(0, calls);
    }
}
