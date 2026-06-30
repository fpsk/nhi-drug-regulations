document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const mobileSearchInput = document.getElementById('mobileSearchInput');
    const mobileClearBtn = document.getElementById('mobileClearBtn');
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const categoryPills = document.getElementById('categoryPills');
    const mobileResultsList = document.getElementById('mobileResultsList');
    const mobileNoResults = document.getElementById('mobileNoResults');
    const mobileStatsCounter = document.getElementById('mobileStatsCounter');
    const mobileAtcExpansion = document.getElementById('mobileAtcExpansion');
    const mobileAtcTags = document.getElementById('mobileAtcTags');
    const mobileTop6Banner = document.getElementById('mobileTop6Banner');
    const mobileLoadMoreContainer = document.getElementById('mobileLoadMoreContainer');
    const mobileLoadMoreBtn = document.getElementById('mobileLoadMoreBtn');

    // Navigation Buttons
    const navHomeBtn = document.getElementById('navHomeBtn');
    const navChaptersBtn = document.getElementById('navChaptersBtn');
    const navUploadBtn = document.getElementById('navUploadBtn');

    // Modals & Sheets
    const mobileDetailSheet = document.getElementById('mobileDetailSheet');
    const closeSheetBtn = document.getElementById('closeSheetBtn');
    const mobileUploadSheet = document.getElementById('mobileUploadSheet');
    const closeUploadSheetBtn = document.getElementById('closeUploadSheetBtn');
    const mobileUploadForm = document.getElementById('mobileUploadForm');
    const mobileFileInput = document.getElementById('mobileFileInput');
    const mobileUploadPassword = document.getElementById('mobileUploadPassword');
    const mobileDropZone = document.getElementById('mobileDropZone');
    const mobileFileSelected = document.getElementById('mobileFileSelected');
    const mobileSelectedFileName = document.getElementById('mobileSelectedFileName');
    const mobileUploadStatus = document.getElementById('mobileUploadStatus');

    let currentOffset = 0;
    let currentLimit = 6;
    let currentChapter = '';
    let currentRegulations = [];
    let debounceTimer = null;

    // Theme Toggle
    let isDark = true;
    themeToggleBtn.addEventListener('click', () => {
        isDark = !isDark;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        themeToggleBtn.innerHTML = isDark ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });

    // Initialize
    performMobileSearch();

    // Search input event
    mobileSearchInput.addEventListener('input', () => {
        mobileClearBtn.classList.toggle('hidden', !mobileSearchInput.value);
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentOffset = 0;
            performMobileSearch();
            checkMobileATC();
        }, 300);
    });

    mobileClearBtn.addEventListener('click', () => {
        mobileSearchInput.value = '';
        mobileClearBtn.classList.add('hidden');
        mobileAtcExpansion.classList.add('hidden');
        currentOffset = 0;
        performMobileSearch();
    });

    // Category pills event
    categoryPills.querySelectorAll('.pill').forEach(pill => {
        pill.addEventListener('click', (e) => {
            categoryPills.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
            currentChapter = e.target.getAttribute('data-chap');
            currentOffset = 0;
            performMobileSearch();
        });
    });

    // Bottom Navigation
    navHomeBtn.addEventListener('click', () => {
        setActiveNav(navHomeBtn);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    navChaptersBtn.addEventListener('click', () => {
        setActiveNav(navChaptersBtn);
        categoryPills.scrollIntoView({ behavior: 'smooth' });
    });
    navUploadBtn.addEventListener('click', () => {
        setActiveNav(navUploadBtn);
        mobileUploadSheet.classList.remove('hidden');
    });

    function setActiveNav(btn) {
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }

    // Load More event
    mobileLoadMoreBtn.addEventListener('click', loadMoreMobileResults);

    // Detail sheet tabs
    document.querySelectorAll('.sheet-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            document.querySelectorAll('.sheet-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.sheet-tab-content').forEach(c => c.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById(e.target.getAttribute('data-stab')).classList.add('active');
        });
    });

    closeSheetBtn.addEventListener('click', () => mobileDetailSheet.classList.add('hidden'));
    closeUploadSheetBtn.addEventListener('click', () => mobileUploadSheet.classList.add('hidden'));

    // Upload zone
    mobileDropZone.addEventListener('click', () => mobileFileInput.click());
    mobileFileInput.addEventListener('change', () => {
        if (mobileFileInput.files[0]) {
            mobileSelectedFileName.textContent = mobileFileInput.files[0].name;
            mobileFileSelected.classList.remove('hidden');
        }
    });

    mobileUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!mobileFileInput.files[0]) return;
        const formData = new FormData();
        formData.append('file', mobileFileInput.files[0]);
        formData.append('password', mobileUploadPassword ? mobileUploadPassword.value : '');

        mobileUploadStatus.innerHTML = '<span style="color:#38bdf8;"><i class="fa-solid fa-spinner fa-spin"></i> 正在驗證密碼與解析檔...</span>';
        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                mobileUploadStatus.innerHTML = `<span style="color:#4ade80;"><i class="fa-solid fa-circle-check"></i> ${data.message}</span>`;
                setTimeout(() => {
                    mobileUploadSheet.classList.add('hidden');
                    mobileUploadStatus.innerHTML = '';
                    if (mobileUploadPassword) mobileUploadPassword.value = '';
                    mobileFileSelected.classList.add('hidden');
                    currentOffset = 0;
                    performMobileSearch();
                }, 1500);
            } else {
                mobileUploadStatus.innerHTML = `<span style="color:#f43f5e;">錯誤：${data.message}</span>`;
            }
        } catch (err) {
            mobileUploadStatus.innerHTML = `<span style="color:#f43f5e;">上傳失敗：${err.message}</span>`;
        }
    });

    async function checkMobileATC() {
        const q = mobileSearchInput.value.trim();
        if (!q) { mobileAtcExpansion.classList.add('hidden'); return; }
        try {
            const res = await fetch(`/api/atc/expand?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            if (data.status === 'success' && data.expansions.length > 0) {
                mobileAtcTags.innerHTML = '';
                data.expansions.forEach(exp => {
                    const cardItem = document.createElement('div');
                    cardItem.className = 'mobile-atc-card';
                    
                    let html = `
                        <div class="atc-exp-header" style="display:flex; justify-content:space-between; border-bottom: 1px solid rgba(56, 189, 248, 0.15); padding-bottom: 0.3rem; margin-bottom: 0.3rem;">
                            <span style="font-size:0.75rem; font-weight:700; color:#38bdf8;"><i class="fa-solid fa-barcode"></i> ATC: ${exp.atc_code}</span>
                            <span style="font-size:0.75rem; font-weight:600; color:#93c5fd;"><i class="fa-solid fa-layer-group"></i> 類別: ${exp.class_code}</span>
                        </div>
                        <div style="display:flex; flex-direction:column; gap:0.25rem; font-size:0.8rem;">
                            <div>
                                <span style="color:#94a3b8; font-weight:600; display:inline-block; width:110px;">分類 (ATC Class):</span>
                                <span style="color:#f1f5f9;">${exp.class_name_tc}</span>
                            </div>
                    `;
                    
                    if (exp.ingredient_en || exp.ingredient_tc) {
                        html += `
                            <div>
                                <span style="color:#94a3b8; font-weight:600; display:inline-block; width:110px;">成分 (Generic):</span>
                                <span style="color:#f1f5f9; font-weight:600;">${exp.ingredient_en} ${exp.ingredient_tc ? `(${exp.ingredient_tc})` : ''}</span>
                            </div>
                        `;
                    }
                    
                    if (exp.is_brand) {
                        const brandsList = [];
                        if (exp.brand_en) brandsList.push(`${exp.brand_en} (Eng)`);
                        if (exp.brand_tc && exp.brand_tc.length > 0) brandsList.push(`${exp.brand_tc.join('/')} (中)`);
                        
                        html += `
                            <div>
                                <span style="color:#94a3b8; font-weight:600; display:inline-block; width:110px;">商品名 (Brands):</span>
                                <span style="color:#f1f5f9;">${brandsList.join(' | ')}</span>
                            </div>
                        `;
                    }
                    
                    html += `</div>`;
                    cardItem.innerHTML = html;
                    mobileAtcTags.appendChild(cardItem);
                });
                mobileAtcExpansion.classList.remove('hidden');
            } else {
                mobileAtcExpansion.classList.add('hidden');
            }
        } catch (err) { console.error("ATC error:", err); }
    }


    async function performMobileSearch() {
        const q = mobileSearchInput.value.trim();
        mobileStatsCounter.textContent = '搜尋中...';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&chapter=${encodeURIComponent(currentChapter)}&limit=${currentLimit}&offset=${currentOffset}`);
            const data = await res.json();

            if (data.status === 'success') {
                currentRegulations = data.results;

                if (data.is_limited) {
                    mobileStatsCounter.textContent = `共 ${data.total_count} 筆依相關度排序，顯示前 ${data.count} 項`;
                    mobileTop6Banner.innerHTML = `<i class="fa-solid fa-fire-flame-curved"></i> 共 ${data.total_count} 項，已自動精準排序顯示前 ${data.count} 項最佳規定：`;
                    mobileTop6Banner.classList.remove('hidden');
                } else {
                    mobileStatsCounter.textContent = `共找到 ${data.total_count || data.count} 筆規定`;
                    mobileTop6Banner.classList.add('hidden');
                }

                mobileLoadMoreContainer.classList.toggle('hidden', !data.has_more);
                renderMobileCards(data.results, false);
            }
        } catch (err) {
            console.error("Mobile search error:", err);
            mobileStatsCounter.textContent = '搜尋發生錯誤';
        }
    }

    async function loadMoreMobileResults() {
        const q = mobileSearchInput.value.trim();
        currentOffset += currentLimit;
        mobileLoadMoreBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 載入更多中...';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&chapter=${encodeURIComponent(currentChapter)}&limit=${currentLimit}&offset=${currentOffset}`);
            const data = await res.json();

            if (data.status === 'success') {
                currentRegulations = currentRegulations.concat(data.results);
                mobileLoadMoreContainer.classList.toggle('hidden', !data.has_more);
                mobileLoadMoreBtn.innerHTML = '<i class="fa-solid fa-angles-down"></i> 顯示更多規定 (Load More)';
                renderMobileCards(data.results, true);
            }
        } catch (err) {
            console.error("Load more error:", err);
            mobileLoadMoreBtn.innerHTML = '<i class="fa-solid fa-angles-down"></i> 顯示更多規定 (Load More)';
        }
    }

    function renderMobileCards(regulations, isAppend) {
        if (!isAppend) mobileResultsList.innerHTML = '';

        if (regulations.length === 0 && !isAppend) {
            mobileNoResults.classList.remove('hidden');
            return;
        }
        mobileNoResults.classList.add('hidden');

        const existingCount = isAppend ? mobileResultsList.children.length : 0;

        regulations.forEach((reg, idx) => {
            const card = document.createElement('div');
            card.className = 'm-card';

            const labs = reg.conditions_of_payment.laboratory_criteria || [];
            const labBadges = labs.map(l => `<span class="m-tag-lab"><i class="fa-solid fa-flask"></i> ${l}</span>`).join(' ');

            const indications = reg.conditions_of_payment.indications || [];
            const indicationBadges = indications.map(ind => `<span class="m-tag-ind"><i class="fa-solid fa-notes-medical"></i> ${ind}</span>`).join(' ');

            card.innerHTML = `
                <div class="m-card-header">
                    <span class="m-badge">#${existingCount + idx + 1} ${reg.section_number}</span>
                    <span class="m-chapter">${reg.chapter.split(' ')[0]}</span>
                </div>
                <h3 class="m-title">${reg.section_title}</h3>
                <div class="m-tags-group">${indicationBadges} ${labBadges}</div>
                <p class="m-summary">${cleanSummaryText(reg.conditions_of_payment.summary)}</p>
                <div class="m-card-footer">
                    <button class="btn-m-detail" data-id="${reg.regulation_id}">
                        <i class="fa-solid fa-circle-info"></i> 給付條件標註
                    </button>
                </div>
            `;

            card.querySelector('.btn-m-detail').addEventListener('click', () => openMobileSheet(reg));
            mobileResultsList.appendChild(card);
        });
    }

    function cleanSummaryText(text) {
        if (!text) return '';
        return text.replace(/【給付與評估表格.*?】:\s*/g, '').replace(/\|/g, ' - ').substring(0, 200) + '...';
    }

    function openMobileSheet(reg) {
        document.getElementById('sheetSecBadge').textContent = reg.section_number;
        document.getElementById('sheetTitle').textContent = reg.section_title;
        document.getElementById('sheetChapter').textContent = reg.chapter;
        document.getElementById('sheetDates').textContent = reg.effective_dates.length ? reg.effective_dates.join(', ') : '未特別標註';

        const sheetFullText = document.getElementById('sheetFullText');
        renderFormattedText(sheetFullText, reg.reference_annotations.full_text);

        if (window.jsyaml) {
            document.getElementById('sheetOkfYaml').textContent = jsyaml.dump(reg);
        } else {
            document.getElementById('sheetOkfYaml').textContent = JSON.stringify(reg, null, 2);
        }

        mobileDetailSheet.classList.remove('hidden');
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
