document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const searchInput = document.getElementById('searchInput');
    const clearSearch = document.getElementById('clearSearch');
    const chapterFilter = document.getElementById('chapterFilter');
    const labFilter = document.getElementById('labFilter');
    const resultsGrid = document.getElementById('resultsGrid');
    const noResults = document.getElementById('noResults');
    const statsCounter = document.getElementById('statsCounter');
    const atcExpansion = document.getElementById('atcExpansion');
    const atcTags = document.getElementById('atcTags');
    const top6Banner = document.getElementById('top6Banner');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    const loadMoreBtn = document.getElementById('loadMoreBtn');

    // Modals
    const detailModal = document.getElementById('detailModal');
    const closeModal = document.getElementById('closeModal');
    const uploadModal = document.getElementById('uploadModal');
    const uploadBtn = document.getElementById('uploadBtn');
    const closeUploadModal = document.getElementById('closeUploadModal');
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadPassword = document.getElementById('uploadPassword');
    const dropZone = document.getElementById('dropZone');
    const fileSelected = document.getElementById('fileSelected');
    const selectedFileName = document.getElementById('selectedFileName');
    const uploadStatus = document.getElementById('uploadStatus');

    let currentOffset = 0;
    let currentLimit = 6;
    let currentRegulations = [];
    let debounceTimer = null;

    // Initialize
    loadChapters();
    performSearch();

    // Event Listeners
    searchInput.addEventListener('input', () => {
        clearSearch.style.display = searchInput.value ? 'block' : 'none';
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentOffset = 0;
            performSearch();
            checkATCExpansion();
        }, 300);
    });

    clearSearch.addEventListener('click', () => {
        searchInput.value = '';
        clearSearch.style.display = 'none';
        atcExpansion.classList.add('hidden');
        currentOffset = 0;
        performSearch();
    });

    chapterFilter.addEventListener('change', () => { currentOffset = 0; performSearch(); });
    labFilter.addEventListener('change', () => { currentOffset = 0; performSearch(); });

    loadMoreBtn.addEventListener('click', () => {
        loadMoreResults();
    });

    // Modal tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            e.target.classList.add('active');
            const tabId = e.target.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    closeModal.addEventListener('click', () => detailModal.classList.add('hidden'));
    closeUploadModal.addEventListener('click', () => uploadModal.classList.add('hidden'));
    uploadBtn.addEventListener('click', () => uploadModal.classList.remove('hidden'));

    // File Drop Zone
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#38bdf8';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'rgba(56, 189, 248, 0.4)';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });
    fileInput.addEventListener('change', handleFileSelect);

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files[0]) return;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('password', uploadPassword ? uploadPassword.value : '');

        uploadStatus.innerHTML = '<span style="color:#38bdf8;"><i class="fa-solid fa-spinner fa-spin"></i> 正在驗證密碼並解析檔案...</span>';
        
        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.status === 'success') {
                uploadStatus.innerHTML = `<span style="color:#4ade80;"><i class="fa-solid fa-circle-check"></i> ${data.message} (${data.records_count} 筆規範已更新)</span>`;
                setTimeout(() => {
                    uploadModal.classList.add('hidden');
                    uploadStatus.innerHTML = '';
                    if (uploadPassword) uploadPassword.value = '';
                    fileSelected.classList.add('hidden');
                    loadChapters();
                    currentOffset = 0;
                    performSearch();
                }, 1500);
            } else {
                uploadStatus.innerHTML = `<span style="color:#f43f5e;"><i class="fa-solid fa-triangle-exclamation"></i> 錯誤：${data.message}</span>`;
            }
        } catch (err) {
            uploadStatus.innerHTML = `<span style="color:#f43f5e;"><i class="fa-solid fa-triangle-exclamation"></i> 上傳失敗：${err.message}</span>`;
        }
    });

    function handleFileSelect() {
        if (fileInput.files[0]) {
            selectedFileName.textContent = fileInput.files[0].name;
            fileSelected.classList.remove('hidden');
        }
    }

    async function loadChapters() {
        try {
            const res = await fetch('/api/chapters');
            const data = await res.json();
            if (data.status === 'success') {
                chapterFilter.innerHTML = '<option value="">全部章節 (All Chapters)</option>';
                data.chapters.forEach(chap => {
                    const opt = document.createElement('option');
                    opt.value = chap;
                    opt.textContent = chap;
                    chapterFilter.appendChild(opt);
                });
            }
        } catch (err) {
            console.error("Error loading chapters:", err);
        }
    }

    async function checkATCExpansion() {
        const q = searchInput.value.trim();
        if (!q) {
            atcExpansion.classList.add('hidden');
            return;
        }
        try {
            const res = await fetch(`/api/atc/expand?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            if (data.status === 'success' && data.expansions.length > 0) {
                atcTags.innerHTML = '';
                data.expansions.forEach(exp => {
                    const tag = document.createElement('div');
                    tag.className = 'atc-tag';
                    tag.innerHTML = `<strong>${exp.atc_code}</strong> | ${exp.class_name_tc} (${exp.class_name_en})`;
                    atcTags.appendChild(tag);
                });
                atcExpansion.classList.remove('hidden');
            } else {
                atcExpansion.classList.add('hidden');
            }
        } catch (err) {
            console.error("Error expanding ATC:", err);
        }
    }

    async function performSearch() {
        const q = searchInput.value.trim();
        const chap = chapterFilter.value;
        const lab = labFilter.value;

        statsCounter.textContent = '搜尋中...';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&chapter=${encodeURIComponent(chap)}&lab=${encodeURIComponent(lab)}&limit=${currentLimit}&offset=${currentOffset}`);
            const data = await res.json();
            
            if (data.status === 'success') {
                currentRegulations = data.results;
                
                if (data.is_limited) {
                    statsCounter.textContent = `共 ${data.total_count} 筆依相關度排序，顯示前 ${data.count} 項`;
                    top6Banner.innerHTML = `<i class="fa-solid fa-fire-flame-curved"></i> 搜尋結果共 ${data.total_count} 項，已依據給付適應症與臨床藥理相關度排序，精準顯示前 ${data.count} 項最佳候選規定：`;
                    top6Banner.classList.remove('hidden');
                } else {
                    statsCounter.textContent = `共找到 ${data.total_count || data.count} 筆規定`;
                    top6Banner.classList.add('hidden');
                }

                if (data.has_more) {
                    loadMoreContainer.classList.remove('hidden');
                } else {
                    loadMoreContainer.classList.add('hidden');
                }

                renderResults(data.results, false);
            }
        } catch (err) {
            console.error("Search error:", err);
            statsCounter.textContent = '搜尋發生錯誤';
        }
    }

    async function loadMoreResults() {
        const q = searchInput.value.trim();
        const chap = chapterFilter.value;
        const lab = labFilter.value;
        
        currentOffset += currentLimit;
        loadMoreBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 載入更多中...';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&chapter=${encodeURIComponent(chap)}&lab=${encodeURIComponent(lab)}&limit=${currentLimit}&offset=${currentOffset}`);
            const data = await res.json();
            
            if (data.status === 'success') {
                currentRegulations = currentRegulations.concat(data.results);
                
                if (data.has_more) {
                    loadMoreContainer.classList.remove('hidden');
                    loadMoreBtn.innerHTML = '<i class="fa-solid fa-angles-down"></i> 顯示更多給付規定 (Load More)';
                } else {
                    loadMoreContainer.classList.add('hidden');
                }

                renderResults(data.results, true);
            }
        } catch (err) {
            console.error("Load more error:", err);
            loadMoreBtn.innerHTML = '<i class="fa-solid fa-angles-down"></i> 顯示更多給付規定 (Load More)';
        }
    }

    function renderResults(regulations, isAppend) {
        if (!isAppend) {
            resultsGrid.innerHTML = '';
        }
        
        if (regulations.length === 0 && !isAppend) {
            noResults.classList.remove('hidden');
            return;
        }
        noResults.classList.add('hidden');

        const existingCount = isAppend ? resultsGrid.children.length : 0;

        regulations.forEach((reg, idx) => {
            const card = document.createElement('div');
            card.className = 'card';
            
            const labs = reg.conditions_of_payment.laboratory_criteria || [];
            const labBadges = labs.map(l => `<span class="badge-lab"><i class="fa-solid fa-flask"></i> ${l}</span>`).join(' ');
            
            const indications = reg.conditions_of_payment.indications || [];
            const indicationBadges = indications.map(ind => `<span class="badge-indication"><i class="fa-solid fa-notes-medical"></i> ${ind}</span>`).join(' ');

            card.innerHTML = `
                <div>
                    <div class="card-header">
                        <span class="sec-badge">#${existingCount + idx + 1} ${reg.section_number}</span>
                        <span class="chapter-tag">${reg.chapter.split(' ')[0]}</span>
                    </div>
                    <h3 class="card-title">${reg.section_title}</h3>
                    <div class="badge-group">${indicationBadges} ${labBadges}</div>
                    <p class="card-summary">${cleanSummaryText(reg.conditions_of_payment.summary)}</p>
                </div>
                <div class="card-footer">
                    <button class="btn btn-secondary btn-detail" data-id="${reg.regulation_id}">
                        <i class="fa-solid fa-circle-info"></i> 給付條件與內文標註
                    </button>
                </div>
            `;
            
            card.querySelector('.btn-detail').addEventListener('click', () => openDetailModal(reg));
            resultsGrid.appendChild(card);
        });
    }

    function cleanSummaryText(text) {
        if (!text) return '';
        return text.replace(/【給付與評估表格.*?】:\s*/g, '').replace(/\|/g, ' - ').substring(0, 260) + '...';
    }

    function openDetailModal(reg) {
        document.getElementById('modalSecBadge').textContent = reg.section_number;
        document.getElementById('modalTitle').textContent = reg.section_title;
        document.getElementById('modalChapter').textContent = reg.chapter;
        document.getElementById('modalDates').textContent = reg.effective_dates.length ? reg.effective_dates.join(', ') : '未特別標註';
        
        const fullTextContainer = document.getElementById('modalFullText');
        renderFormattedText(fullTextContainer, reg.reference_annotations.full_text);
        
        if (window.jsyaml) {
            document.getElementById('modalOkfYaml').textContent = jsyaml.dump(reg);
        } else {
            document.getElementById('modalOkfYaml').textContent = JSON.stringify(reg, null, 2);
        }

        detailModal.classList.remove('hidden');
    }

    function renderFormattedText(container, text) {
        if (!text) { container.innerHTML = ''; return; }
        
        let lines = text.split('\n');
        let htmlParts = [];
        let inTable = false;
        let tableRows = [];

        lines.forEach(line => {
            let trimmed = line.trim();
            if (trimmed.includes('|')) {
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                tableRows.push(trimmed);
            } else {
                if (inTable) {
                    inTable = false;
                    htmlParts.push(buildTableHtml(tableRows));
                    tableRows = [];
                }
                if (trimmed) {
                    if (trimmed.startsWith('【')) {
                        htmlParts.push(`<h4 style="color:#38bdf8; margin-top:1rem;"><i class="fa-solid fa-table-list"></i> ${escapeHtml(trimmed)}</h4>`);
                    } else {
                        htmlParts.push(`<p style="margin-bottom:0.5rem;">${escapeHtml(trimmed)}</p>`);
                    }
                }
            }
        });

        if (inTable) {
            htmlParts.push(buildTableHtml(tableRows));
        }

        container.innerHTML = htmlParts.join('');
    }

    function buildTableHtml(rows) {
        if (!rows.length) return '';
        let html = '<div class="table-responsive"><table class="clinical-table">';
        rows.forEach((rowStr, idx) => {
            let cells = rowStr.split('|').map(c => c.trim());
            if (idx === 0) {
                html += '<thead><tr>' + cells.map(c => `<th>${escapeHtml(c)}</th>`).join('') + '</tr></thead><tbody>';
            } else {
                html += '<tr>' + cells.map(c => `<td>${escapeHtml(c)}</td>`).join('') + '</tr>';
            }
        });
        html += '</tbody></table></div>';
        return html;
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
});
