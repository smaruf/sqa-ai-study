// Level 3 - Advanced: SpecFlow BDD Step Definitions in C#
// =========================================================
//
// NuGet: SpecFlow, SpecFlow.NUnit, SpecFlow.Tools.MsBuild.Generation
//
// Run:  dotnet test --verbosity normal

using NUnit.Framework;
using TechTalk.SpecFlow;

namespace Sqa.Level3;

// ── Simple AuthService (SUT) ──────────────────────────────────────────────────

public class AuthService
{
    private readonly Dictionary<string, (string Password, string Name)> _users = new();

    public void Register(string email, string password, string name) =>
        _users[email] = (password, name);

    public Dictionary<string, string> Login(string email, string password)
    {
        if (!_users.TryGetValue(email, out var user) || user.Password != password)
            throw new UnauthorizedAccessException("Invalid credentials");

        return new() { ["token"] = $"tok_{email}", ["name"] = user.Name };
    }
}

// ── Step definitions ──────────────────────────────────────────────────────────

[Binding]
public class LoginSteps
{
    private AuthService                    _service     = null!;
    private Dictionary<string, string>?   _loginResult;
    private Exception?                     _loginError;
    private string                         _email       = "";
    private string                         _password    = "";

    [BeforeScenario]
    public void SetUp()
    {
        _service     = new AuthService();
        _loginResult = null;
        _loginError  = null;
    }

    [Given(@"a registered user with email ""(.*)"" and password ""(.*)""")]
    public void GivenARegisteredUser(string email, string password)
    {
        _service.Register(email, password, "Test User");
        _email    = email;
        _password = password;
    }

    [When(@"they log in with the correct password")]
    public void WhenTheyLogInWithCorrectPassword()
    {
        try
        {
            _loginResult = _service.Login(_email, _password);
            _loginError  = null;
        }
        catch (Exception ex)
        {
            _loginResult = null;
            _loginError  = ex;
        }
    }

    [When(@"they log in with the wrong password ""(.*)""")]
    public void WhenTheyLogInWithWrongPassword(string wrongPassword)
    {
        try
        {
            _loginResult = _service.Login(_email, wrongPassword);
            _loginError  = null;
        }
        catch (Exception ex)
        {
            _loginResult = null;
            _loginError  = ex;
        }
    }

    [Then(@"they should receive a valid auth token")]
    public void ThenShouldReceiveToken()
    {
        Assert.That(_loginResult, Is.Not.Null);
        Assert.That(_loginResult!["token"], Does.StartWith("tok_"));
    }

    [Then(@"they should see an invalid credentials error")]
    public void ThenShouldSeeError()
    {
        Assert.That(_loginError, Is.Not.Null);
        Assert.That(_loginError!.Message, Does.Contain("Invalid credentials"));
    }

    [Then(@"they should not receive a token")]
    public void ThenShouldNotReceiveToken()
    {
        Assert.That(_loginResult, Is.Null);
    }
}
