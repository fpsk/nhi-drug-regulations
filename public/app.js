document.addEventListener('DOMContentLoaded', () => {
    const {
        escapeHtml,
        cleanTitleForDisplay,
        formatDatesForDisplay,
        cleanSummaryText,
        renderFormattedText,
        resolveActiveHighlights,
        autoScrollToFirstMatch,
        populateModalDrugs,
        buildCardBadgesHtml,
        renderStructuredCriteria,
        fetchSearch,
        submitUpload,
    } = window.NHIShared;

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
    const currentLimit = 6;
    let currentRegulations = [];
    let currentHighlightTerms = [];
    let debounceTimer = null;
    let searchAbortController = null;

    loadChapters();
    performSearch();

    searchInput.addEventListener('input', () => {
        clearSearch.style.display = searchInput.value ? 'block' : 'none';
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentOffset = 0;
            performSearch();
        }, 220);
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
    loadMoreBtn.addEventListener('click', loadMoreResults);

    closeModal.addEventListener('click', () => detailModal.classList.add('hidden'));
    closeUploadModal.addEventListener('click', () => uploadModal.classList.add('hidden'));
    uploadBtn.addEventListener('click', () => uploadModal.classList.remove('hidden'));

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            detailModal.classList.add('hidden');
            uploadModal.classList.add('hidden');
        }
    });
    detailModal.addEventListener('click', (e) => {
        if (e.target === detailModal) detailModal.classList.add('hidden');
    });
    uploadModal.addEventListener('click', (e) => {
        if (e.target === uploadModal) uploadModal.classList.add('hidden');
    });

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

    function handleFileSelect() {
        if (fileInput.files[0]) {
            selectedFileName.textContent = fileInput.files[0].name;
            fileSelected.classList.remove('hidden');
        }
    }

    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitUpload({
            file: fileInput.files[0],
            password: uploadPassword ? uploadPassword.value : '',
            statusEl: uploadStatus,
            onSuccess: () => {
                uploadModal.classList.add('hidden');
                uploadStatus.innerHTML = '';
                if (uploadPassword) uploadPassword.value = '';
                fileSelected.classList.add('hidden');
                loadChapters();
                currentOffset = 0;
                performSearch();
            },
        });
    });

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

    function renderATCExpansions(expansions) {
        if (!expansions || expansions.length === 0) {
            atcExpansion.classList.add('hidden');
            return;
        }
        atcTags.innerHTML = '';
        expansions.forEach(exp => {
            const cardItem = document.createElement('div');
            cardItem.className = 'atc-expansion-card';

            const primaryJumpBtn = exp.primary_regulation
                ? `<button class="btn-jump-reg" data-sec="${escapeHtml(exp.primary_regulation)}" style="background:rgba(16,185,129,0.2); border:1px solid rgba(16,185,129,0.45); color:#6ee7b7; border-radius:4px; padding:0.15rem 0.5rem; font-size:0.75rem; font-weight:600; cursor:pointer;"><i class="fa-solid fa-bullseye"></i> 主規定 ${escapeHtml(exp.primary_regulation)}</button>`
                : '';

            let html = `
                <div class="atc-exp-header">
                    <span class="atc-exp-code-badge"><i class="fa-solid fa-barcode"></i> 藥物完整 ATC 碼: ${escapeHtml(exp.atc_code)}</span>
                    <div style="display:flex; gap:0.4rem; align-items:center;">
                        ${primaryJumpBtn}
                        <span class="atc-exp-class-badge"><i class="fa-solid fa-layer-group"></i> 藥理分類: ${escapeHtml(exp.class_code)}</span>
                    </div>
                </div>
                <div class="atc-exp-body">
                    <div class="atc-exp-row">
                        <span class="atc-exp-label">藥理分類與給付規定 (ATC Class):</span>
                        <span class="atc-exp-value"><strong>${escapeHtml(exp.class_name_tc)}</strong> <small style="opacity: 0.8; display: block;">${escapeHtml(exp.class_name_en)}</small></span>
                    </div>
            `;

            if (exp.ingredient_en || exp.ingredient_tc) {
                html += `
                    <div class="atc-exp-row">
                        <span class="atc-exp-label">對應成分 (Generic Ingredient):</span>
                        <span class="atc-exp-value"><strong>${escapeHtml(exp.ingredient_en)}</strong> ${exp.ingredient_tc ? `(${escapeHtml(exp.ingredient_tc)})` : ''}</span>
                    </div>
                `;
            }

            if (exp.brand_en || (exp.brand_tc && exp.brand_tc.length > 0)) {
                const brandsList = [];
                if (exp.brand_en) brandsList.push(`<strong>${escapeHtml(exp.brand_en)}</strong> (英文)`);
                if (exp.brand_tc && exp.brand_tc.length > 0) brandsList.push(`<strong>${escapeHtml(exp.brand_tc.join(', '))}</strong> (台灣品牌)`);

                html += `
                    <div class="atc-exp-row">
                        <span class="atc-exp-label">商品名稱 (Trade Brands):</span>
                        <span class="atc-exp-value">${brandsList.join(' | ')}</span>
                    </div>
                `;
            }

            html += `</div>`;
            cardItem.innerHTML = html;

            const jumpBtn = cardItem.querySelector('.btn-jump-reg');
            if (jumpBtn) {
                jumpBtn.addEventListener('click', () => {
                    searchInput.value = jumpBtn.getAttribute('data-sec');
                    clearSearch.style.display = 'block';
                    currentOffset = 0;
                    performSearch();
                });
            }

            atcTags.appendChild(cardItem);
        });
        atcExpansion.classList.remove('hidden');
    }

    async function performSearch() {
        const q = searchInput.value.trim();
        const chap = chapterFilter.value;
        const lab = labFilter.value;

        statsCounter.textContent = '搜尋中...';

        if (searchAbortController) {
            searchAbortController.abort();
        }
        searchAbortController = new AbortController();

        try {
            const data = await fetchSearch({
                q,
                chapter: chap,
                lab,
                limit: currentLimit,
                offset: currentOffset,
                signal: searchAbortController.signal,
            });

            if (data.status === 'success') {
                currentRegulations = data.results;
                currentHighlightTerms = data.highlight_terms || [];

                if (data.is_limited) {
                    statsCounter.textContent = `共 ${data.total_count} 筆依相關度排序，顯示前 ${data.count} 項`;
                    top6Banner.innerHTML = `<i class="fa-solid fa-fire-flame-curved"></i> 搜尋結果共 ${data.total_count} 項，已依據給付適應症與臨床藥理相關度排序，精準顯示前 ${data.count} 項最佳候選規定：`;
                    top6Banner.classList.remove('hidden');
                } else {
                    statsCounter.textContent = `共找到 ${data.total_count || data.count} 筆規定`;
                    top6Banner.classList.add('hidden');
                }

                loadMoreContainer.classList.toggle('hidden', !data.has_more);
                renderATCExpansions(q ? (data.atc_expansions || []) : []);
                renderResults(data.results, false);
            }
        } catch (err) {
            if (err.name === 'AbortError') return;
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
            const data = await fetchSearch({
                q,
                chapter: chap,
                lab,
                limit: currentLimit,
                offset: currentOffset,
            });

            if (data.status === 'success') {
                currentRegulations = currentRegulations.concat(data.results);
                loadMoreContainer.classList.toggle('hidden', !data.has_more);
                loadMoreBtn.innerHTML = '<i class="fa-solid fa-angles-down"></i> 顯示更多給付規定 (Load More)';
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

            const { displayTitle, priorAuthBadge, drugBadges, indicationBadges, labBadges } = buildCardBadgesHtml(reg, {
                maxBios: 5,
                maxDrugs: 5,
                labClass: 'badge-lab',
                indClass: 'badge-indication',
            });

            card.innerHTML = `
                <div>
                    <div class="card-header">
                        <span class="sec-badge">#${existingCount + idx + 1} ${escapeHtml(reg.section_number)}</span>
                        <div style="display:flex; gap:0.4rem; align-items:center;">
                            ${priorAuthBadge}
                            <span class="chapter-tag">${escapeHtml(reg.chapter.split(' ')[0])}</span>
                        </div>
                    </div>
                    <h3 class="card-title">${escapeHtml(displayTitle)}</h3>
                    <div class="badge-group">${drugBadges} ${indicationBadges} ${labBadges}</div>
                    <p class="card-summary">${escapeHtml(cleanSummaryText(reg.conditions_of_payment.summary, 360))}</p>
                </div>
                <div class="card-footer">
                    <button class="btn btn-secondary btn-detail" data-id="${escapeHtml(reg.regulation_id)}">
                        <i class="fa-solid fa-circle-info"></i> 給付條件與內文標註
                    </button>
                </div>
            `;

            card.querySelector('.btn-detail').addEventListener('click', () => openDetailModal(reg));
            resultsGrid.appendChild(card);
        });
    }

    function openDetailModal(reg) {
        document.getElementById('modalSecBadge').textContent = reg.section_number;
        document.getElementById('modalTitle').textContent = cleanTitleForDisplay(reg.section_title);
        document.getElementById('modalChapter').textContent = reg.chapter;
        document.getElementById('modalDates').textContent = formatDatesForDisplay(reg.effective_dates);

        populateModalDrugs(
            document.getElementById('modalDrugsBox'),
            document.getElementById('modalDrugsList'),
            reg
        );

        const fullTextContainer = document.getElementById('modalFullText');
        renderStructuredCriteria({
            reg,
            criteriaSection: document.getElementById('modalStructuredCriteriaSection'),
            chipsContainer: document.getElementById('modalStructuredChips'),
            priorAuthEl: document.getElementById('modalPriorAuthBadge'),
            fullTextContainer,
            anchorPrefix: 'clause-sec',
            maxRuleLen: 28,
        });

        const activeHighlights = resolveActiveHighlights(searchInput.value, currentHighlightTerms);
        renderFormattedText(
            fullTextContainer,
            reg.reference_annotations.full_text,
            activeHighlights.length > 0 ? activeHighlights : null,
            'clause-sec'
        );

        detailModal.classList.remove('hidden');

        if (activeHighlights.length > 0) {
            autoScrollToFirstMatch(fullTextContainer, 80);
        }
    }
});
