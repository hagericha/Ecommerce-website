document.addEventListener("DOMContentLoaded", function() {
  const searchInput = document.getElementById("search-input");
  const autocompleteList = document.getElementById("autocomplete-list");

  searchInput.addEventListener("input", function() {
    const query = this.value;
    // Clear previous suggestions
    autocompleteList.innerHTML = "";
    if (!query) return;

    // Fetch suggestions from the server
    fetch(`/autocomplete?query=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        data.forEach(item => {
          const div = document.createElement("div");
          div.classList.add("autocomplete-item");
          div.textContent = item.name;
          // Optionally store the product id
          div.dataset.id = item.id;
          div.addEventListener("click", function() {
            // Navigate to the product detail page when suggestion is clicked
            window.location.href = `/product/${item.id}`;
          });
          autocompleteList.appendChild(div);
        });
      })
      .catch(error => console.error("Error fetching autocomplete suggestions:", error));
  });

  // Optional: Hide suggestions when clicking outside
  document.addEventListener("click", function(e) {
    if (!searchInput.contains(e.target)) {
      autocompleteList.innerHTML = "";
    }
  });
});







//---------------------------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('.account-nav .nav-link');
  const sections = document.querySelectorAll('.account-section');

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      // Remove active class from all navigation links
      navLinks.forEach(l => l.classList.remove('active'));
      // Remove active class from all content sections
      sections.forEach(section => section.classList.remove('active'));
      // Add active class to clicked link and corresponding section
      link.classList.add('active');
      const target = link.getAttribute('data-target');
      document.getElementById(target).classList.add('active');
    });
  });
});


  