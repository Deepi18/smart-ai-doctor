document.addEventListener('DOMContentLoaded', () => {

  // 1. Dark/Light Theme Toggle Handler
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const currentTheme = localStorage.getItem('theme') || 'dark';

  if (currentTheme === 'light') {
    document.body.classList.add('light-theme');
    if (themeToggleBtn) themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      const isLight = document.body.classList.contains('light-theme');
      localStorage.setItem('theme', isLight ? 'light' : 'dark');
      themeToggleBtn.innerHTML = isLight ? '<i class="fa-solid fa-sun me-1"></i> Light Mode' : '<i class="fa-solid fa-moon me-1"></i> Dark Mode';
    });
  }

  // Mobile Sidebar Toggle Handler
  const mobileToggle = document.getElementById('mobileSidebarToggle');
  const sidebarMenu = document.getElementById('sidebarMenu');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  if (mobileToggle && sidebarMenu && sidebarBackdrop) {
    mobileToggle.addEventListener('click', () => {
      sidebarMenu.classList.toggle('show');
      sidebarBackdrop.classList.toggle('show');
    });
    sidebarBackdrop.addEventListener('click', () => {
      sidebarMenu.classList.remove('show');
      sidebarBackdrop.classList.remove('show');
    });
  }

  // 2. Live Symptom Search Filter (Home Page)
  const searchInput = document.getElementById('symptomSearch');
  const symptomTags = document.querySelectorAll('.symptom-tag');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      symptomTags.forEach(tag => {
        const text = tag.textContent.toLowerCase();
        tag.style.display = text.includes(query) ? 'block' : 'none';
      });
    });
  }

  // 3. Category Filter Pills (Home Page)
  const catPills = document.querySelectorAll('.cat-pill');
  if (catPills.length > 0) {
    fetch('/api/symptoms')
      .then(res => res.json())
      .then(data => {
        const categories = data.categories;
        catPills.forEach(pill => {
          pill.addEventListener('click', () => {
            catPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const selectedCat = pill.getAttribute('data-category');
            if (selectedCat === 'All') {
              symptomTags.forEach(tag => tag.style.display = 'block');
            } else {
              const allowed = categories[selectedCat] || [];
              symptomTags.forEach(tag => {
                const labelText = tag.querySelector('label').textContent.trim();
                tag.style.display = allowed.includes(labelText) ? 'block' : 'none';
              });
            }
          });
        });
      })
      .catch(err => console.log('Symptoms API error:', err));
  }

  // 4. Doctor Search & Specialty Filter (Doctors Page)
  const docSearchInput = document.getElementById('doctorSearchInput');
  const docFilterBtns = document.querySelectorAll('.doc-filter-btn');
  const docItems = document.querySelectorAll('.doc-item');

  function filterDoctors() {
    const query = docSearchInput ? docSearchInput.value.toLowerCase().trim() : '';
    const activeBtn = document.querySelector('.doc-filter-btn.active');
    const selectedSpecialty = activeBtn ? activeBtn.getAttribute('data-specialty') : 'All';

    docItems.forEach(item => {
      const specialty = item.getAttribute('data-specialty');
      const searchData = item.getAttribute('data-search').toLowerCase();

      const matchesSpecialty = (selectedSpecialty === 'All' || specialty.includes(selectedSpecialty));
      const matchesSearch = (!query || searchData.includes(query));

      item.style.display = (matchesSpecialty && matchesSearch) ? 'block' : 'none';
    });
  }

  if (docSearchInput) {
    docSearchInput.addEventListener('input', filterDoctors);
  }

  if (docFilterBtns.length > 0) {
    docFilterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        docFilterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filterDoctors();
      });
    });
  }

  // Doctor Modal Populator
  const bookBtns = document.querySelectorAll('.book-doc-btn');
  bookBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const docId = btn.getAttribute('data-doc-id');
      const docName = btn.getAttribute('data-doc-name');
      document.getElementById('modalDocId').value = docId;
      document.getElementById('modalDocName').value = docName;
    });
  });

  // Doctor Appointment Form Submit
  const appointmentForm = document.getElementById('appointmentForm');
  const bookingResultDiv = document.getElementById('bookingResult');
  if (appointmentForm) {
    appointmentForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(appointmentForm);
      const data = Object.fromEntries(formData.entries());

      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      fetch('/api/appointments', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
      })
      .then(res => res.json())
      .then(resData => {
        if (resData.error) {
          bookingResultDiv.innerHTML = `<span class="text-danger">${resData.error}</span>`;
        } else {
          bookingResultDiv.innerHTML = `
            <div class="alert alert-success border-0 mb-0">
              <i class="fa-solid fa-circle-check"></i> ${resData.message}
            </div>
          `;
          appointmentForm.reset();
        }
      })
      .catch(err => {
        bookingResultDiv.innerHTML = `<span class="text-danger">Failed to submit booking. Try again.</span>`;
      });
    });
  }

  // 5. Medical Knowledge Base Search Filter (Knowledge Page)
  const kbSearchInput = document.getElementById('kbSearchInput');
  const kbCategorySelect = document.getElementById('kbCategorySelect');
  const kbItems = document.querySelectorAll('.kb-card-item');

  function filterKnowledge() {
    const query = kbSearchInput ? kbSearchInput.value.toLowerCase().trim() : '';
    const selectedCat = kbCategorySelect ? kbCategorySelect.value : 'All';

    kbItems.forEach(item => {
      const cat = item.getAttribute('data-category');
      const searchData = item.getAttribute('data-search').toLowerCase();

      const matchesCat = (selectedCat === 'All' || cat === selectedCat);
      const matchesSearch = (!query || searchData.includes(query));

      item.style.display = (matchesCat && matchesSearch) ? 'block' : 'none';
    });
  }

  if (kbSearchInput) kbSearchInput.addEventListener('input', filterKnowledge);
  if (kbCategorySelect) kbCategorySelect.addEventListener('change', filterKnowledge);

  // 6. Delete Assessment History Record AJAX (History Page)
  const deleteBtns = document.querySelectorAll('.delete-history-btn');
  deleteBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const assessmentId = btn.getAttribute('data-id');
      if (confirm(`Are you sure you want to delete Assessment Record #SAD-${assessmentId}?`)) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        fetch(`/api/history/delete/${assessmentId}`, { 
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken }
        })
          .then(res => res.json())
          .then(data => {
            const row = document.getElementById(`history_row_${assessmentId}`);
            if (row) row.remove();
          })
          .catch(err => console.log('Delete history error:', err));
      }
    });
  });

  // 7. BMI Calculator Handler
  const bmiForm = document.getElementById('bmiForm');
  const bmiResultDiv = document.getElementById('bmiResult');

  if (bmiForm) {
    bmiForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const height = parseFloat(document.getElementById('bmiHeight').value);
      const weight = parseFloat(document.getElementById('bmiWeight').value);

      if (!height || !weight || height <= 0 || weight <= 0) {
        bmiResultDiv.innerHTML = `<div class="alert alert-danger border-0 py-2 small mt-2">Please enter valid positive height and weight values.</div>`;
        return;
      }

      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      fetch('/calculate_bmi', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ height, weight })
      })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          bmiResultDiv.innerHTML = `<div class="alert alert-danger border-0 py-2 small mt-2">${data.error}</div>`;
        } else {
          bmiResultDiv.innerHTML = `
            <div class="mt-3 p-3 rounded-3 bg-dark bg-opacity-60 border border-secondary border-opacity-30 text-light shadow">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fs-6 fw-bold">Your BMI Score: <strong style="font-size: 1.4rem; color: ${data.color}">${data.bmi}</strong></span>
                <span class="badge px-3 py-2 rounded-pill font-monospace" style="background-color: ${data.color}25; border: 1px solid ${data.color}; color: ${data.color}">${data.category}</span>
              </div>
              <p class="mb-0 small text-slate-200 mt-2"><i class="fa-solid fa-circle-info text-info me-1"></i> ${data.advice}</p>
            </div>
          `;
        }
      })
      .catch(err => {
        bmiResultDiv.innerHTML = `<div class="alert alert-danger border-0 py-2 small mt-2">Failed to calculate BMI. Please try again.</div>`;
      });
    });
  }

});
