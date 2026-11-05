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
    const currentLimit = 6;
    let currentChapter = '';
    let currentRegulations = [];
    let currentHighlightTerms = [];
    let debounceTimer = null;
    let searchAbortController = null;

    // Theme Toggle
    let isDark = true;
    themeToggleBtn.addEventListener('click', () => {
        isDark = !isDark;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        themeToggleBtn.innerHTML = isDark ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });

    performMobileSearch();

    mobileSearchInput.addEventListener('input', () => {
        mobileClearBtn.classList.toggle('hidden', !mobileSearchInput.value);
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentOffset = 0;
            performMobileSearch();
        }, 220);
    });

    mobileClearBtn.addEventListener('click', () => {
        mobileSearchInput.value = '';
        mobileClearBtn.classList.add('hidden');
        mobileAtcExpansion.classList.add('hidden');
        currentOffset = 0;
        performMobileSearch();
    });

    categoryPills.querySelectorAll('.pill').forEach(pill => {
        pill.addEventListener('click', (e) => {
            categoryPills.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
            currentChapter = e.target.getAttribute('data-chap');
            currentOffset = 0;
            performMobileSearch();
        });
    });

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

    mobileLoadMoreBtn.addEventListener('click', loadMoreMobileResults);
    closeSheetBtn.addEventListener('click', () => mobileDetailSheet.classList.add('hidden'));
    closeUploadSheetBtn.addEventListener('click', () => mobileUploadSheet.classList.add('hidden'));

    mobileDropZone.addEventListener('click', () => mobileFileInput.click());
    mobileFileInput.addEventListener('change', () => {
        if (mobileFileInput.files[0]) {
            mobileSelectedFileName.textContent = mobileFileInput.files[0].name;
            mobileFileSelected.classList.remove('hidden');
        }
    });

    mobileUploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitUpload({
            file: mobileFileInput.files[0],
            password: mobileUploadPassword ? mobileUploadPassword.value : '',
            statusEl: mobileUploadStatus,
            onSuccess: () => {
                mobileUploadSheet.classList.add('hidden');
                mobileUploadStatus.innerHTML = '';
                if (mobileUploadPassword) mobileUploadPassword.value = '';
                mobileFileSelected.classList.add('hidden');
                currentOffset = 0;
                performMobileSearch();
            },
        });
    });

    function renderMobileATC(expansions) {
        if (!expansions || expansions.length === 0) {
            mobileAtcExpansion.classList.add('hidden');
            return;
        }
        mobileAtcTags.innerHTML = '';
        expansions.forEach(exp => {
            const cardItem = document.createElement('div');
            cardItem.className = 'mobile-atc-card';

            let html = `
                <div class="atc-exp-header" style="display:flex; justify-content:space-between; border-bottom: 1px solid rgba(56, 189, 248, 0.15); padding-bottom: 0.3rem; margin-bottom: 0.3rem;">
                    <span style="font-size:0.75rem; font-weight:700; color:#38bdf8;"><i class="fa-solid fa-barcode"></i> ATC: ${escapeHtml(exp.atc_code)}</span>
                    <span style="font-size:0.75rem; font-weight:600; color:#93c5fd;"><i class="fa-solid fa-layer-group"></i> 類別: ${escapeHtml(exp.class_code)}</span>
                </div>
                <div style="display:flex; flex-direction:column; gap:0.25rem; font-size:0.8rem;">
                    <div>
                        <span style="color:#94a3b8; font-weight:600; display:inline-block; width:110px;">分類 (ATC Class):</span>
                        <span style="color:#f1f5f9;">${escapeHtml(exp.class_name_tc)}</span>
                    </div>
            `;

            if (exp.ingredient_en || exp.ingredient_tc) {
                html += `
                    <div>
                        <span style="color:#94a3b8; font-weight:600; display:inline-block; width:110px;">成分 (Generic):</span>
                        <span style="color:#f1f5f9; font-weight:600;">${escapeHtml(exp.ingredient_en)} ${exp.ingredient_tc ? `(${escapeHtml(exp.ingredient_tc)})` : ''}</span>
                    </div>
                `;
            }

            if (exp.brand_en || (exp.brand_tc && exp.brand_tc.length > 0)) {
                const brandsList = [];
                if (exp.brand_en) brandsList.push(`${escapeHtml(exp.brand_en)} (Eng)`);
                if (exp.brand_tc && exp.brand_tc.length > 0) brandsList.push(`${escapeHtml(exp.brand_tc.join(', '))} (台)`);

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
    }

    async function performMobileSearch() {
        const q = mobileSearchInput.value.trim();
        mobileStatsCounter.textContent = '搜尋中...';

        if (searchAbortController) {
            searchAbortController.abort();
        }
        searchAbortController = new AbortController();

        try {
            const data = await fetchSearch({
                q,
                chapter: currentChapter,
                limit: currentLimit,
                offset: currentOffset,
                signal: searchAbortController.signal,
            });

            if (data.status === 'success') {
                currentRegulations = data.results;
                currentHighlightTerms = data.highlight_terms || [];

                if (data.is_limited) {
                    mobileStatsCounter.textContent = `共 ${data.total_count} 筆依相關度排序，顯示前 ${data.count} 項`;
                    mobileTop6Banner.innerHTML = `<i class="fa-solid fa-fire-flame-curved"></i> 共 ${data.total_count} 項，已自動精準排序顯示前 ${data.count} 項最佳規定：`;
                    mobileTop6Banner.classList.remove('hidden');
                } else {
                    mobileStatsCounter.textContent = `共找到 ${data.total_count || data.count} 筆規定`;
                    mobileTop6Banner.classList.add('hidden');
                }

                mobileLoadMoreContainer.classList.toggle('hidden', !data.has_more);
                renderMobileATC(q ? (data.atc_expansions || []) : []);
                renderMobileCards(data.results, false);
            }
        } catch (err) {
            if (err.name === 'AbortError') return;
            console.error("Mobile search error:", err);
            mobileStatsCounter.textContent = '搜尋發生錯誤';
        }
    }

    async function loadMoreMobileResults() {
        const q = mobileSearchInput.value.trim();
        currentOffset += currentLimit;
        mobileLoadMoreBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 載入更多中...';

        try {
            const data = await fetchSearch({
                q,
                chapter: currentChapter,
                limit: currentLimit,
                offset: currentOffset,
            });

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
        const activeHighlights = resolveActiveHighlights(mobileSearchInput.value, currentHighlightTerms);

        regulations.forEach((reg, idx) => {
            const card = document.createElement('div');
            card.className = 'm-card';

            const { displayTitleHtml, priorAuthBadge, drugBadges, indicationBadges, labBadges, summaryHtml } = buildCardBadgesHtml(reg, {
                maxBios: 4,
                maxDrugs: 4,
                labClass: 'm-tag-lab',
                indClass: 'm-tag-ind',
                highlightTarget: activeHighlights.length > 0 ? activeHighlights : null,
                summaryMaxLen: 200,
            });

            card.innerHTML = `
                <div class="m-card-header">
                    <span class="m-badge">#${existingCount + idx + 1} ${escapeHtml(reg.section_number)}</span>
                    <div style="display:flex; gap:0.35rem; align-items:center;">
                        ${priorAuthBadge}
                        <span class="m-chapter">${escapeHtml(reg.chapter.split(' ')[0])}</span>
                    </div>
                </div>
                <h3 class="m-title">${displayTitleHtml}</h3>
                <div class="m-tags-group">${drugBadges} ${indicationBadges} ${labBadges}</div>
                <p class="m-summary">${summaryHtml}</p>
                <div class="m-card-footer">
                    <button class="btn-m-detail" data-id="${escapeHtml(reg.regulation_id)}">
                        <i class="fa-solid fa-circle-info"></i> 給付條件標註
                    </button>
                </div>
            `;

            card.querySelector('.btn-m-detail').addEventListener('click', () => openMobileSheet(reg));
            mobileResultsList.appendChild(card);
        });
    }

    function openMobileSheet(reg) {
        document.getElementById('sheetSecBadge').textContent = reg.section_number;
        document.getElementById('sheetTitle').textContent = cleanTitleForDisplay(reg.section_title);
        document.getElementById('sheetChapter').textContent = reg.chapter;
        document.getElementById('sheetDates').textContent = formatDatesForDisplay(reg.effective_dates);

        populateModalDrugs(
            document.getElementById('sheetDrugsBox'),
            document.getElementById('sheetDrugsList'),
            reg
        );

        const sheetFullText = document.getElementById('sheetFullText');
        renderStructuredCriteria({
            reg,
            criteriaSection: document.getElementById('sheetStructuredCriteriaSection'),
            chipsContainer: document.getElementById('sheetStructuredChips'),
            priorAuthEl: document.getElementById('sheetPriorAuthBadge'),
            fullTextContainer: sheetFullText,
            anchorPrefix: 'm-clause-sec',
            maxRuleLen: 22,
        });

        const activeHighlights = resolveActiveHighlights(mobileSearchInput.value, currentHighlightTerms);
        renderFormattedText(
            sheetFullText,
            reg.reference_annotations.full_text,
            activeHighlights.length > 0 ? activeHighlights : null,
            'm-clause-sec'
        );

        mobileDetailSheet.classList.remove('hidden');

        if (activeHighlights.length > 0) {
            autoScrollToFirstMatch(sheetFullText, 80);
        }
    }
});
