using Lab01.BT;
using NUnit.Framework;

public class BTTests
{
    [Test]
    public void Selector_ReturnsFirstNonFailure()
    {
        var sel = new Selector(new Condition(() => false), new Action(() => Status.Running));
        Assert.AreEqual(Status.Running, sel.Tick());
    }

    [Test]
    public void Sequence_StopsOnFailure()
    {
        int calls = 0;
        var seq = new Sequence(new Condition(() => false), new Action(() => { calls++; return Status.Success; }));
        Assert.AreEqual(Status.Failure, seq.Tick());
        Assert.AreEqual(0, calls);
    }
}
