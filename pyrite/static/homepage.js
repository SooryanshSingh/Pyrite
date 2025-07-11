document.addEventListener("DOMContentLoaded", async function () {
  const logoutButton = document.getElementById("logout");
  const signinButton = document.getElementById("signin");
  const signupButton = document.getElementById("signup");

  const supabaseurl = window.config.SUPABASE_URL;
  const supabasekey = window.config.SUPABASE_KEY;

  const supabaseclient = supabase.createClient(supabaseurl, supabasekey);

  // Logout function
  async function logout() {
    const { error } = await supabaseclient.auth.signOut();

    if (error) {
      console.error('Error logging out:', error.message);
    } else {
      alert('User logged out successfully');
      window.location.href = '/homepage';
    }
  }

  // Check user login status when page loads
  const { data: { user }, error } = await supabaseclient.auth.getUser();

  if (user) {
    console.log("User is logged in:", user);

    // Show logout, hide signin/signup
    logoutButton.style.display = 'inline-block';
    signinButton.style.display = 'none';
    signupButton.style.display = 'none';
  } else {
    console.log("No user is logged in");

    // Show signin/signup, hide logout
    logoutButton.style.display = 'none';
    signinButton.style.display = 'inline-block';
    signupButton.style.display = 'inline-block';
  }

  // Add event listener for logout button
  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }
});
