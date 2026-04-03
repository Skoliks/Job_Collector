// Базовый адрес backend API. При необходимости поменяйте порт/хост.
const BASE_URL = "http://127.0.0.1:8000";

// По 10 вакансий на страницу по условию задачи.
const PAGE_SIZE = 10;

// Текущее состояние интерфейса.
const state = {
  currentPage: 1,
  lastPageLoadedCount: 0,
  filters: {
    title: "",
    company: "",
    location: "",
    salary: "",
    sort_by: ""
  },
  editingId: null
};

const elements = {
  parseBtn: document.getElementById("parseBtn"),
  notification: document.getElementById("notification"),
  searchForm: document.getElementById("searchForm"),
  searchInput: document.getElementById("searchInput"),
  searchField: document.getElementById("searchField"),
  companyFilter: document.getElementById("companyFilter"),
  locationFilter: document.getElementById("locationFilter"),
  salaryFilter: document.getElementById("salaryFilter"),
  sortByFilter: document.getElementById("sortByFilter"),
  resetFiltersBtn: document.getElementById("resetFiltersBtn"),
  createForm: document.getElementById("createForm"),
  vacanciesList: document.getElementById("vacanciesList"),
  emptyState: document.getElementById("emptyState"),
  pagination: document.getElementById("pagination")
};

// Универсальный helper для fetch с обработкой ошибок.
async function request(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    let message = `Ошибка ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        message = Array.isArray(errorData.detail)
          ? errorData.detail.map((item) => item.msg || JSON.stringify(item)).join(", ")
          : errorData.detail;
      }
    } catch (_) {
      // Если ответ не JSON, оставляем сообщение по умолчанию.
    }
    throw new Error(message);
  }

  // Для данного API ответы в JSON.
  return response.json();
}

// ----- API-функции (каждый endpoint отдельной функцией) -----

async function fetchVacancies(params = {}) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      query.set(key, String(value));
    }
  });

  // Предположение: backend использует маршрут /vacancies/.
  return request(`${BASE_URL}/vacancies/?${query.toString()}`);
}

async function parseFakeVacancies() {
  return request(`${BASE_URL}/vacancies/parse-fake`, {
    method: "POST"
  });
}

async function createVacancy(payload) {
  return request(`${BASE_URL}/vacancies/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

async function updateVacancy(id, payload) {
  // Используем PATCH, потому что в этом backend PATCH обновляет все поля по необходимости.
  return request(`${BASE_URL}/vacancies/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

async function removeVacancy(id) {
  return request(`${BASE_URL}/vacancies/${id}`, {
    method: "DELETE"
  });
}

// ----- UI helper-функции -----

function showNotification(message, type = "success") {
  elements.notification.textContent = message;
  elements.notification.className = `notification ${type}`;

  setTimeout(() => {
    elements.notification.className = "notification hidden";
    elements.notification.textContent = "";
  }, 3000);
}

function escapeHtml(text = "") {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function truncateText(text = "", maxLength = 180) {
  if (!text) return "Описание не указано";
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

function formatMeta(label, value) {
  return `<span><strong>${label}:</strong> ${escapeHtml(value || "не указано")}</span>`;
}

function renderVacancies(vacancies) {
  elements.vacanciesList.innerHTML = "";

  if (!vacancies.length) {
    elements.emptyState.classList.remove("hidden");
    return;
  }

  elements.emptyState.classList.add("hidden");

  vacancies.forEach((vacancy) => {
    const card = document.createElement("article");
    card.className = "card vacancy-card";

    const hasUrl = Boolean(vacancy.url);
    const titleHtml = hasUrl
      ? `<a href="${escapeHtml(vacancy.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(vacancy.title)}</a>`
      : escapeHtml(vacancy.title || "Без названия");

    card.innerHTML = `
      <h3>${titleHtml}</h3>
      <div class="meta">
        ${formatMeta("Компания", vacancy.company)}
        ${formatMeta("Локация", vacancy.location)}
        ${formatMeta("Зарплата", vacancy.salary)}
        ${formatMeta("Дата публикации", vacancy.published_date)}
      </div>
      <p class="description">${escapeHtml(truncateText(vacancy.description))}</p>
      <div class="card-actions">
        <button class="btn" data-action="edit" data-id="${vacancy.id}">Редактировать</button>
        <button class="btn btn-danger" data-action="delete" data-id="${vacancy.id}">Удалить</button>
      </div>
      <div id="edit-${vacancy.id}"></div>
    `;

    elements.vacanciesList.append(card);
  });
}

function renderPagination() {
  elements.pagination.innerHTML = "";

  const canShowNext = state.lastPageLoadedCount === PAGE_SIZE;
  const maxPage = canShowNext ? state.currentPage + 1 : state.currentPage;

  for (let page = 1; page <= maxPage; page += 1) {
    const button = document.createElement("button");
    button.className = `btn page-btn ${page === state.currentPage ? "active" : ""}`;
    button.textContent = page;
    button.type = "button";

    button.addEventListener("click", () => {
      if (page === state.currentPage) return;
      state.currentPage = page;
      loadVacancies();
    });

    elements.pagination.append(button);
  }
}

function getSearchAndFilters() {
  return {
    title: state.filters.title,
    company: state.filters.company,
    location: state.filters.location,
    salary: state.filters.salary,
    sort_by: state.filters.sort_by,
    limit: PAGE_SIZE,
    offset: (state.currentPage - 1) * PAGE_SIZE
  };
}

function fillEditForm(container, vacancy) {
  container.innerHTML = `
    <form class="grid-form edit-form" data-edit-form="${vacancy.id}">
      <label>
        title*
        <input name="title" type="text" required value="${escapeHtml(vacancy.title || "")}" />
      </label>
      <label>
        company*
        <input name="company" type="text" required value="${escapeHtml(vacancy.company || "")}" />
      </label>
      <label>
        salary
        <input name="salary" type="number" min="0" step="1" value="${vacancy.salary ?? ""}" />
      </label>
      <label>
        location
        <input name="location" type="text" value="${escapeHtml(vacancy.location || "")}" />
      </label>
      <label>
        published_date
        <input name="published_date" type="text" value="${escapeHtml(vacancy.published_date || "")}" />
      </label>
      <label>
        url
        <input name="url" type="url" value="${escapeHtml(vacancy.url || "")}" />
      </label>
      <label class="full-width">
        description
        <textarea name="description" rows="3">${escapeHtml(vacancy.description || "")}</textarea>
      </label>
      <div class="actions">
        <button type="submit" class="btn btn-primary">Сохранить</button>
        <button type="button" class="btn" data-cancel-edit="${vacancy.id}">Отмена</button>
      </div>
    </form>
  `;
}

function normalizeVacancyPayload(formData) {
  const salaryRaw = formData.get("salary");

  return {
    title: formData.get("title")?.trim(),
    company: formData.get("company")?.trim(),
    salary: salaryRaw ? Number(salaryRaw) : null,
    location: formData.get("location")?.trim() || null,
    published_date: formData.get("published_date")?.trim() || null,
    description: formData.get("description")?.trim() || null,
    url: formData.get("url")?.trim() || null
  };
}

// ----- Основная загрузка списка -----

async function loadVacancies() {
  try {
    const params = getSearchAndFilters();
    const vacancies = await fetchVacancies(params);

    state.lastPageLoadedCount = vacancies.length;
    renderVacancies(vacancies);
    renderPagination();
  } catch (error) {
    showNotification(`Ошибка загрузки: ${error.message}`, "error");
    elements.vacanciesList.innerHTML = "";
    elements.emptyState.classList.remove("hidden");
    elements.pagination.innerHTML = "";
  }
}

// ----- Обработчики событий -----

elements.parseBtn.addEventListener("click", async () => {
  try {
    elements.parseBtn.disabled = true;
    const result = await parseFakeVacancies();

    const created = result.created_count ?? 0;
    const skipped = result.skipped_count ?? 0;

    showNotification(`Парсинг завершен: добавлено ${created}, пропущено ${skipped}`);
    state.currentPage = 1;
    await loadVacancies();
  } catch (error) {
    showNotification(`Ошибка парсинга: ${error.message}`, "error");
  } finally {
    elements.parseBtn.disabled = false;
  }
});

elements.searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const searchValue = elements.searchInput.value.trim();
  const searchField = elements.searchField.value;

  // Очищаем целевые поля поиска перед применением нового запроса.
  state.filters.title = "";
  state.filters.company = "";
  state.filters.location = "";
  state.filters.salary = "";

  // Поиск направляем в выбранное поле backend-фильтра.
  if (searchValue) {
    if (searchField === "salary") {
      state.filters.salary = Number(searchValue) || "";
    } else {
      state.filters[searchField] = searchValue;
    }
  }

  // Дополнительные фильтры с формы применяются поверх поиска.
  if (elements.companyFilter.value.trim()) {
    state.filters.company = elements.companyFilter.value.trim();
  }

  if (elements.locationFilter.value.trim()) {
    state.filters.location = elements.locationFilter.value.trim();
  }

  if (elements.salaryFilter.value.trim()) {
    state.filters.salary = Number(elements.salaryFilter.value.trim()) || "";
  }

  state.filters.sort_by = elements.sortByFilter.value;
  state.currentPage = 1;

  await loadVacancies();
});

elements.resetFiltersBtn.addEventListener("click", async () => {
  elements.searchForm.reset();
  state.filters = {
    title: "",
    company: "",
    location: "",
    salary: "",
    sort_by: ""
  };
  state.currentPage = 1;
  await loadVacancies();
});

elements.createForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    const formData = new FormData(elements.createForm);
    const payload = normalizeVacancyPayload(formData);

    await createVacancy(payload);
    elements.createForm.reset();

    showNotification("Вакансия добавлена");
    state.currentPage = 1;
    await loadVacancies();
  } catch (error) {
    showNotification(`Ошибка добавления: ${error.message}`, "error");
  }
});

elements.vacanciesList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const action = target.getAttribute("data-action");
  const vacancyId = Number(target.getAttribute("data-id"));

  if (action === "delete" && vacancyId) {
    const confirmed = confirm("Удалить вакансию?");
    if (!confirmed) return;

    try {
      await removeVacancy(vacancyId);
      showNotification("Вакансия удалена");
      await loadVacancies();
    } catch (error) {
      showNotification(`Ошибка удаления: ${error.message}`, "error");
    }
  }

  if (action === "edit" && vacancyId) {
    try {
      // Для точного редактирования подгружаем карточку заново из списка текущей страницы.
      const currentVacancies = await fetchVacancies(getSearchAndFilters());
      const vacancy = currentVacancies.find((item) => item.id === vacancyId);
      if (!vacancy) {
        showNotification("Не удалось открыть форму редактирования", "error");
        return;
      }

      state.editingId = vacancyId;
      const container = document.getElementById(`edit-${vacancyId}`);
      if (!container) return;

      fillEditForm(container, vacancy);
    } catch (error) {
      showNotification(`Ошибка редактирования: ${error.message}`, "error");
    }
  }

  const cancelEditId = Number(target.getAttribute("data-cancel-edit"));
  if (cancelEditId) {
    const container = document.getElementById(`edit-${cancelEditId}`);
    if (container) container.innerHTML = "";
    state.editingId = null;
  }
});

elements.vacanciesList.addEventListener("submit", async (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;

  if (!form.hasAttribute("data-edit-form")) return;

  event.preventDefault();

  const vacancyId = Number(form.getAttribute("data-edit-form"));
  if (!vacancyId) return;

  try {
    const formData = new FormData(form);
    const payload = normalizeVacancyPayload(formData);

    await updateVacancy(vacancyId, payload);
    showNotification("Вакансия обновлена");
    state.editingId = null;
    await loadVacancies();
  } catch (error) {
    showNotification(`Ошибка обновления: ${error.message}`, "error");
  }
});

// Первая загрузка данных при открытии страницы.
loadVacancies();
