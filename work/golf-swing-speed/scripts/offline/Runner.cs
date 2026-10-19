using System; using System.Linq; using System.Reflection; using NUnit.Framework;
static class Runner { static int Main() { int pass=0, fail=0;
  foreach (var type in typeof(Runner).Assembly.GetTypes().Where(t => t.Namespace=="GolfArcade.Tests"))
    foreach (var m in type.GetMethods()) {
      var cases = m.GetCustomAttributes<TestCaseAttribute>().Select(c => c.Arguments).ToList();
      if (m.GetCustomAttribute<TestAttribute>() != null) cases.Add(new object[0]);
      foreach (var args in cases) {
        string name = $"{type.Name}.{m.Name}({string.Join(",", args)})";
        try { m.Invoke(Activator.CreateInstance(type), args.Select((a,i)=> a is IConvertible && m.GetParameters()[i].ParameterType != a.GetType() && !m.GetParameters()[i].ParameterType.IsEnum ? Convert.ChangeType(a, m.GetParameters()[i].ParameterType) : a).ToArray()); pass++; Console.WriteLine("PASS " + name); }
        catch (TargetInvocationException e) { fail++; Console.WriteLine("FAIL " + name + ": " + e.InnerException.Message.Split('\n')[0]); }
      } }
  Console.WriteLine($"{pass} passed, {fail} failed"); return fail; } }
