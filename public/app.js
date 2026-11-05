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
    let currentHighlightTerms = [];
    let debounceTimer = null;
    let searchAbortController = null;

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

    loadMoreBtn.addEventListener('click', () => {
        loadMoreResults();
    });

    closeModal.addEventListener('click', () => detailModal.classList.add('hidden'));
    closeUploadModal.addEventListener('click', () => uploadModal.classList.add('hidden'));
    uploadBtn.addEventListener('click', () => uploadModal.classList.remove('hidden'));

    // Close modals on Escape key or backdrop click
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
        const signal = searchAbortController.signal;

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&chapter=${encodeURIComponent(chap)}&lab=${encodeURIComponent(lab)}&limit=${currentLimit}&offset=${currentOffset}`, { signal });
            const data = await res.json();
            
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

                if (data.has_more) {
                    loadMoreContainer.classList.remove('hidden');
                } else {
                    loadMoreContainer.classList.add('hidden');
                }

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
            
            const structuredBios = reg.conditions_of_payment.structured_biomarkers || [];
            let labBadges = '';
            if (structuredBios.length > 0) {
                const seenBios = new Set();
                const uniqueBios = [];
                structuredBios.forEach(b => {
                    const key = `${b.biomarker}${b.operator}${b.value}`;
                    if (!seenBios.has(key)) {
                        seenBios.add(key);
                        uniqueBios.push(b);
                    }
                });
                labBadges = uniqueBios.slice(0, 5).map(b => {
                    const snippetText = b.source_grounding ? (b.source_grounding.snippet || b.source_grounding.matched_text || '') : '';
                    const opStr = b.operator === 'status' ? '' : escapeHtml(b.operator);
                    const valStr = escapeHtml(String(b.value));
                    const unitStr = b.unit ? ' ' + escapeHtml(b.unit) : '';
                    return `<span class="badge-biomarker" title="點擊內文可定位原始依據: ${escapeHtml(snippetText)}"><i class="fa-solid fa-vial-circle-check"></i> ${escapeHtml(b.biomarker)} ${opStr}${valStr}${unitStr}</span>`;
                }).join(' ');
            } else {
                const labs = reg.conditions_of_payment.laboratory_criteria || [];
                labBadges = labs.map(l => `<span class="badge-lab"><i class="fa-solid fa-flask"></i> ${escapeHtml(l)}</span>`).join(' ');
            }
            
            const priorAuthBadge = reg.conditions_of_payment.prior_authorization_required 
                ? `<span class="badge-prior-auth" title="本藥品需事前審查核准"><i class="fa-solid fa-stamp"></i> 事前審查</span>` 
                : '';

            const indications = reg.conditions_of_payment.indications || [];
            const indicationBadges = indications.map(ind => `<span class="badge-indication"><i class="fa-solid fa-notes-medical"></i> ${escapeHtml(ind)}</span>`).join(' ');

            const displayTitle = cleanTitleForDisplay(reg.section_title);
            const ingredients = (reg.medications && reg.medications.ingredients) ? reg.medications.ingredients : [];
            let drugBadges = '';
            if (ingredients.length > 0 && !/[A-Za-z]{4,}/.test(displayTitle)) {
                drugBadges = ingredients.slice(0, 5).map(ing => `<span class="badge-lab" style="border-color:rgba(56,189,248,0.35); color:#38bdf8;"><i class="fa-solid fa-pills"></i> ${escapeHtml(ing)}</span>`).join(' ');
            }

            card.innerHTML = `
                <div>
                    <div class="card-header">
                        <span class="sec-badge">#${existingCount + idx + 1} ${reg.section_number}</span>
                        <div style="display:flex; gap:0.4rem; align-items:center;">
                            ${priorAuthBadge}
                            <span class="chapter-tag">${reg.chapter.split(' ')[0]}</span>
                        </div>
                    </div>
                    <h3 class="card-title">${displayTitle}</h3>
                    <div class="badge-group">${drugBadges} ${indicationBadges} ${labBadges}</div>
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

    function cleanTitleForDisplay(title) {
        if (!title) return '';
        return title.replace(/（[^）]*\d+[^）]*）/g, '')
                    .replace(/\([^)]*\d+[^)]*\)/g, '')
                    .trim();
    }

    function formatDatesForDisplay(dates) {
        if (!dates || dates.length === 0) return '未特別標註';
        if (dates.length <= 2) return dates.join(', ');
        return `${dates[0]} ... ${dates[dates.length - 1]} (共 ${dates.length} 次修訂)`;
    }

    function cleanSummaryText(text) {
        if (!text) return '';
        const cleaned = text.replace(/【給付與評估表格.*?】:\s*/g, '').replace(/\|/g, ' - ');
        return cleaned.length > 360 ? cleaned.substring(0, 360) + '...' : cleaned;
    }

    function openDetailModal(reg) {
        document.getElementById('modalSecBadge').textContent = reg.section_number;
        document.getElementById('modalTitle').textContent = cleanTitleForDisplay(reg.section_title);
        document.getElementById('modalChapter').textContent = reg.chapter;
        document.getElementById('modalDates').textContent = formatDatesForDisplay(reg.effective_dates);

        const modalDrugsBox = document.getElementById('modalDrugsBox');
        const modalDrugsList = document.getElementById('modalDrugsList');
        if (modalDrugsBox && modalDrugsList) {
            const ings = (reg.medications && reg.medications.ingredients) ? reg.medications.ingredients : [];
            const classes = (reg.medications && reg.medications.drug_classes) ? reg.medications.drug_classes : [];
            const combined = ings.length > 0 ? ings : classes;
            if (combined.length > 0) {
                modalDrugsList.textContent = combined.join(', ');
                modalDrugsBox.classList.remove('hidden');
            } else {
                modalDrugsBox.classList.add('hidden');
            }
        }
        
        // Render LangExtract Structured Criteria & Grounding Chips
        const criteriaSection = document.getElementById('modalStructuredCriteriaSection');
        const chipsContainer = document.getElementById('modalStructuredChips');
        const priorAuthEl = document.getElementById('modalPriorAuthBadge');
        
        if (criteriaSection && chipsContainer) {
            chipsContainer.innerHTML = '';
            const bios = reg.conditions_of_payment.structured_biomarkers || [];
            const steps = reg.conditions_of_payment.step_therapy || [];
            const stops = reg.conditions_of_payment.stopping_rules || [];
            const evals = reg.conditions_of_payment.evaluation_intervals || [];
            const priorAuth = reg.conditions_of_payment.prior_authorization_required;
            const priorAuthGrounding = reg.conditions_of_payment.prior_authorization_grounding;

            if (priorAuth) {
                priorAuthEl.innerHTML = `<span class="badge-prior-auth" style="cursor:pointer;" id="priorAuthChip"><i class="fa-solid fa-stamp"></i> 需事前審查 (點擊定位)</span>`;
                const paMatch = priorAuthGrounding ? (priorAuthGrounding.snippet || priorAuthGrounding.matched_text || '') : '事前審查';
                if (paMatch) {
                    const paBtn = priorAuthEl.querySelector('#priorAuthChip');
                    if (paBtn) {
                        paBtn.addEventListener('click', () => {
                            scrollToHighlight(reg.reference_annotations.full_text, paMatch);
                        });
                    }
                }
            } else {
                priorAuthEl.innerHTML = '';
            }

            let hasAnyStructured = bios.length > 0 || steps.length > 0 || stops.length > 0 || evals.length > 0 || priorAuth;
            if (hasAnyStructured) {
                criteriaSection.classList.remove('hidden');

                // Deduplicate identical biomarker chips while keeping all occurrence snippets for cycling
                const groupedBios = [];
                const bioMap = new Map();
                bios.forEach((b) => {
                    const key = `${b.biomarker}|${b.operator}|${b.value}|${b.unit || ''}`;
                    const snippetText = b.source_grounding ? (b.source_grounding.snippet || b.source_grounding.matched_text || '') : '';
                    if (!bioMap.has(key)) {
                        const entry = { ...b, snippets: snippetText ? [snippetText] : [], clickIdx: 0 };
                        bioMap.set(key, entry);
                        groupedBios.push(entry);
                    } else if (snippetText) {
                        bioMap.get(key).snippets.push(snippetText);
                    }
                });

                groupedBios.forEach((b) => {
                    const chip = document.createElement('button');
                    chip.className = 'criteria-chip';
                    const countBadge = b.snippets.length > 1 ? ` <span style="opacity:0.75; font-size:0.72rem;">(×${b.snippets.length})</span>` : '';
                    chip.title = b.snippets.length > 0 ? `點擊定位原文 (${b.snippets.length} 處): ${b.snippets[0]}` : '點擊定位原文';
                    chip.innerHTML = `<i class="fa-solid fa-vial" style="color:#10b981;"></i> <strong>${escapeHtml(b.biomarker)}</strong> ${escapeHtml(b.operator === 'status' ? '' : b.operator)} ${escapeHtml(String(b.value))}${b.unit ? ' ' + escapeHtml(b.unit) : ''}${countBadge}`;
                    chip.addEventListener('click', () => {
                        document.querySelectorAll('.criteria-chip').forEach(c => c.classList.remove('active'));
                        chip.classList.add('active');
                        if (b.snippets.length > 0) {
                            const idx = b.clickIdx % b.snippets.length;
                            const targetSnippet = b.snippets[idx];
                            // Count which occurrence of targetSnippet this corresponds to
                            let sameSnippetOcc = 0;
                            for (let i = 0; i < idx; i++) {
                                if (b.snippets[i] === targetSnippet) sameSnippetOcc++;
                            }
                            b.clickIdx++;
                            scrollToHighlight(reg.reference_annotations.full_text, targetSnippet, sameSnippetOcc);
                        }
                    });
                    chipsContainer.appendChild(chip);
                });

                evals.forEach((ev) => {
                    const chip = document.createElement('button');
                    chip.className = 'criteria-chip';
                    const evLabel = typeof ev === 'string' ? ev : (ev.schedule || ev.frequency || '');
                    const evSnippet = typeof ev === 'string' ? ev : (ev.source_grounding ? (ev.source_grounding.snippet || ev.source_grounding.matched_text) : evLabel);
                    chip.innerHTML = `<i class="fa-regular fa-clock" style="color:#38bdf8;"></i> 評估/續用: ${escapeHtml(evLabel)}`;
                    chip.addEventListener('click', () => {
                        document.querySelectorAll('.criteria-chip').forEach(c => c.classList.remove('active'));
                        chip.classList.add('active');
                        if (evSnippet) {
                            scrollToHighlight(reg.reference_annotations.full_text, evSnippet);
                        }
                    });
                    chipsContainer.appendChild(chip);
                });

                steps.slice(0, 3).forEach((st) => {
                    const chip = document.createElement('button');
                    chip.className = 'criteria-chip';
                    const stLabel = typeof st === 'string' ? st : (st.rule || st.requirement || '');
                    const stSnippet = typeof st === 'string' ? st : (st.source_grounding ? (st.source_grounding.snippet || st.source_grounding.matched_text) : stLabel);
                    const shortRule = stLabel.length > 28 ? stLabel.substring(0, 28) + '...' : stLabel;
                    chip.innerHTML = `<i class="fa-solid fa-stairs" style="color:#f59e0b;"></i> 二線/轉換條件: ${escapeHtml(shortRule)}`;
                    chip.addEventListener('click', () => {
                        document.querySelectorAll('.criteria-chip').forEach(c => c.classList.remove('active'));
                        chip.classList.add('active');
                        if (stSnippet) {
                            scrollToHighlight(reg.reference_annotations.full_text, stSnippet);
                        }
                    });
                    chipsContainer.appendChild(chip);
                });

                stops.slice(0, 3).forEach((sp) => {
                    const chip = document.createElement('button');
                    chip.className = 'criteria-chip';
                    const spLabel = typeof sp === 'string' ? sp : (sp.rule || sp.condition || '');
                    const spSnippet = typeof sp === 'string' ? sp : (sp.source_grounding ? (sp.source_grounding.snippet || sp.source_grounding.matched_text) : spLabel);
                    const shortRule = spLabel.length > 28 ? spLabel.substring(0, 28) + '...' : spLabel;
                    chip.innerHTML = `<i class="fa-solid fa-ban" style="color:#ef4444;"></i> 停藥/排除: ${escapeHtml(shortRule)}`;
                    chip.addEventListener('click', () => {
                        document.querySelectorAll('.criteria-chip').forEach(c => c.classList.remove('active'));
                        chip.classList.add('active');
                        if (spSnippet) {
                            scrollToHighlight(reg.reference_annotations.full_text, spSnippet);
                        }
                    });
                    chipsContainer.appendChild(chip);
                });
            } else {
                criteriaSection.classList.add('hidden');
            }
        }

        const fullTextContainer = document.getElementById('modalFullText');
        const rawSegments = searchInput.value.trim().split(/[,，;；]+/).map(s => s.trim()).filter(s => s.length >= 2);
        const activeHighlights = (searchInput.value.trim() && currentHighlightTerms.length > 0) ? currentHighlightTerms : rawSegments;
        renderFormattedText(fullTextContainer, reg.reference_annotations.full_text, activeHighlights.length > 0 ? activeHighlights : null);

        detailModal.classList.remove('hidden');

        if (activeHighlights.length > 0) {
            setTimeout(() => {
                const targetEl = fullTextContainer.querySelector('.clause-header-matched') || fullTextContainer.querySelector('.grounding-highlight');
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 80);
        }
    }

    function scrollToHighlight(fullText, highlightSnippet, occurrenceIdx = 0) {
        const fullTextContainer = document.getElementById('modalFullText');
        renderFormattedText(fullTextContainer, fullText, highlightSnippet);
        setTimeout(() => {
            const marks = fullTextContainer.querySelectorAll('.grounding-highlight');
            if (marks.length > 0) {
                const target = marks[Math.min(occurrenceIdx, marks.length - 1)];
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 60);
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function createHighlightRegex(highlightTarget) {
        if (!highlightTarget) return null;
        if (Array.isArray(highlightTarget)) {
            const patterns = highlightTarget
                .map(t => escapeHtml(String(t).trim()))
                .filter(t => t.length >= 2)
                .sort((a, b) => b.length - a.length)
                .map(t => {
                    const parts = t.split(/\s+/).filter(Boolean).map(p => escapeRegExp(p));
                    return parts.join('[\\s\\u3000]*');
                })
                .filter(Boolean);
            if (patterns.length === 0) return null;
            return new RegExp(`(${patterns.join('|')})`, 'gi');
        }
        const escaped = escapeHtml(String(highlightTarget).trim());
        const parts = escaped.split(/\s+/).filter(Boolean).map(p => escapeRegExp(p));
        if (parts.length === 0) return null;
        return new RegExp(`(${parts.join('[\\s\\u3000]*')})`, 'gi');
    }

    function renderFormattedText(container, text, highlightSnippet = null) {
        if (!text) { container.innerHTML = ''; return; }
        
        let lines = text.split('\n');
        let htmlParts = [];
        let inTable = false;
        let tableRows = [];
        let clauseNavItems = [];
        const regex = createHighlightRegex(highlightSnippet);
        const primaryTerm = Array.isArray(highlightSnippet) && highlightSnippet.length > 0 ? highlightSnippet[0].toLowerCase() : null;
        const clauseHeaderRe = /^[（\(](\d+)[）\)]\s*([^：:\n]{2,32}?)[：:](.*)$/;

        lines.forEach((line, lineIdx) => {
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
                    htmlParts.push(buildTableHtml(tableRows, highlightSnippet));
                    tableRows = [];
                }
                if (trimmed) {
                    const clauseMatch = trimmed.match(clauseHeaderRe);
                    let safeLine = escapeHtml(trimmed);
                    if (regex) {
                        safeLine = safeLine.replace(regex, `<mark class="grounding-highlight">$1</mark>`);
                    }
                    if (clauseMatch) {
                        const cNum = clauseMatch[1];
                        const cTitle = clauseMatch[2].trim();
                        const anchorId = `clause-sec-${cNum}-${lineIdx}`;
                        const isMatched = Boolean(
                            (primaryTerm && cTitle.toLowerCase().includes(primaryTerm)) ||
                            (regex && cTitle.match(createHighlightRegex(highlightSnippet)))
                        );
                        clauseNavItems.push({ num: cNum, title: cTitle, anchorId, matched: isMatched });
                        htmlParts.push(`<div id="${anchorId}" class="clause-header ${isMatched ? 'clause-header-matched' : ''}">${safeLine}</div>`);
                    } else if (trimmed.startsWith('【')) {
                        htmlParts.push(`<h4 style="color:#38bdf8; margin-top:1rem;"><i class="fa-solid fa-table-list"></i> ${safeLine}</h4>`);
                    } else {
                        htmlParts.push(`<p style="margin-bottom:0.5rem;">${safeLine}</p>`);
                    }
                }
            }
        });

        if (inTable) {
            htmlParts.push(buildTableHtml(tableRows, highlightSnippet));
        }

        let navHtml = '';
        if (clauseNavItems.length >= 2) {
            const pillsHtml = clauseNavItems.map(item =>
                `<button type="button" class="clause-jump-pill ${item.matched ? 'matched' : ''}" data-target="${item.anchorId}">(${escapeHtml(item.num)}) ${escapeHtml(item.title)}</button>`
            ).join('');
            navHtml = `
                <div class="clause-jump-bar">
                    <span class="clause-jump-label"><i class="fa-solid fa-compass"></i> 條文段落快速跳轉 (點擊定位)：</span>
                    <div class="clause-jump-pills">${pillsHtml}</div>
                </div>
            `;
        }

        container.innerHTML = navHtml + htmlParts.join('');

        container.querySelectorAll('.clause-jump-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-target');
                const targetEl = document.getElementById(targetId);
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    targetEl.classList.add('clause-header-matched');
                }
            });
        });
    }

    function buildTableHtml(rows, highlightSnippet = null) {
        if (!rows.length) return '';
        let html = '<div class="table-responsive"><table class="clinical-table">';
        rows.forEach((rowStr, idx) => {
            let cells = rowStr.split('|').map(c => c.trim());
            const formatCell = (c) => {
                let s = escapeHtml(c);
                if (highlightSnippet) {
                    const regex = createHighlightRegex(highlightSnippet);
                    if (regex) {
                        s = s.replace(regex, `<mark class="grounding-highlight">$1</mark>`);
                    }
                }
                return s;
            };
            if (idx === 0) {
                html += '<thead><tr>' + cells.map(c => `<th>${formatCell(c)}</th>`).join('') + '</tr></thead><tbody>';
            } else {
                html += '<tr>' + cells.map(c => `<td>${formatCell(c)}</td>`).join('') + '</tr>';
            }
        });
        html += '</tbody></table></div>';
        return html;
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
});
