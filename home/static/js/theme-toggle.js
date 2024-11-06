// Wait until the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Check if the user has a saved theme preference
    const currentTheme = localStorage.getItem('theme') || 'nord';
    document.documentElement.setAttribute('data-theme', currentTheme);
  
    // Set up the theme toggle
    const themeToggleIcon = document.getElementById('theme-toggle');
  
    if (themeToggleIcon) { // Check if the element exists
      // Function to toggle themes
      themeToggleIcon.addEventListener('click', () => {
        const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'nord' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
  
        // Toggle icon class
        if (newTheme === 'dark') {
          themeToggleIcon.classList.remove('fa-moon');
          themeToggleIcon.classList.add('fa-sun');
        } else {
          themeToggleIcon.classList.remove('fa-sun');
          themeToggleIcon.classList.add('fa-moon');
        }
      });
    } else {
      console.log('Theme toggle icon not found');
    }
  });
  

