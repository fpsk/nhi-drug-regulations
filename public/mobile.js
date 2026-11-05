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

    // Initialize
    performMobileSearch();

    // Search input event
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
        const signal = searchAbortController.signal;

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&chapter=${encodeURIComponent(currentChapter)}&limit=${currentLimit}&offset=${currentOffset}`, { signal });
            const data = await res.json();

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
                labBadges = uniqueBios.slice(0, 4).map(b => {
                    const opStr = b.operator === 'status' ? '' : escapeHtml(b.operator);
                    const valStr = escapeHtml(String(b.value));
                    const unitStr = b.unit ? ' ' + escapeHtml(b.unit) : '';
                    return `<span class="badge-biomarker"><i class="fa-solid fa-vial-circle-check"></i> ${escapeHtml(b.biomarker)} ${opStr}${valStr}${unitStr}</span>`;
                }).join(' ');
            } else {
                const labs = reg.conditions_of_payment.laboratory_criteria || [];
                labBadges = labs.map(l => `<span class="m-tag-lab"><i class="fa-solid fa-flask"></i> ${escapeHtml(l)}</span>`).join(' ');
            }

            const priorAuthBadge = reg.conditions_of_payment.prior_authorization_required 
                ? `<span class="badge-prior-auth"><i class="fa-solid fa-stamp"></i> 事前審查</span>` 
                : '';

            const indications = reg.conditions_of_payment.indications || [];
            const indicationBadges = indications.map(ind => `<span class="m-tag-ind"><i class="fa-solid fa-notes-medical"></i> ${escapeHtml(ind)}</span>`).join(' ');

            const displayTitle = cleanTitleForDisplay(reg.section_title);
            const ingredients = (reg.medications && reg.medications.ingredients) ? reg.medications.ingredients : [];
            let drugBadges = '';
            if (ingredients.length > 0 && !/[A-Za-z]{4,}/.test(displayTitle)) {
                drugBadges = ingredients.slice(0, 4).map(ing => `<span class="m-tag-lab" style="border-color:rgba(56,189,248,0.35); color:#38bdf8;"><i class="fa-solid fa-pills"></i> ${escapeHtml(ing)}</span>`).join(' ');
            }

            card.innerHTML = `
                <div class="m-card-header">
                    <span class="m-badge">#${existingCount + idx + 1} ${reg.section_number}</span>
                    <div style="display:flex; gap:0.35rem; align-items:center;">
                        ${priorAuthBadge}
                        <span class="m-chapter">${reg.chapter.split(' ')[0]}</span>
                    </div>
                </div>
                <h3 class="m-title">${displayTitle}</h3>
                <div class="m-tags-group">${drugBadges} ${indicationBadges} ${labBadges}</div>
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
        return text.replace(/【給付與評估表格.*?】:\s*/g, '').replace(/\|/g, ' - ').substring(0, 200) + '...';
    }

    function openMobileSheet(reg) {
        document.getElementById('sheetSecBadge').textContent = reg.section_number;
        document.getElementById('sheetTitle').textContent = cleanTitleForDisplay(reg.section_title);
        document.getElementById('sheetChapter').textContent = reg.chapter;
        document.getElementById('sheetDates').textContent = formatDatesForDisplay(reg.effective_dates);

        const sheetDrugsBox = document.getElementById('sheetDrugsBox');
        const sheetDrugsList = document.getElementById('sheetDrugsList');
        if (sheetDrugsBox && sheetDrugsList) {
            const ings = (reg.medications && reg.medications.ingredients) ? reg.medications.ingredients : [];
            const classes = (reg.medications && reg.medications.drug_classes) ? reg.medications.drug_classes : [];
            const combined = ings.length > 0 ? ings : classes;
            if (combined.length > 0) {
                sheetDrugsList.textContent = combined.join(', ');
                sheetDrugsBox.classList.remove('hidden');
            } else {
                sheetDrugsBox.classList.add('hidden');
            }
        }

        const criteriaSection = document.getElementById('sheetStructuredCriteriaSection');
        const chipsContainer = document.getElementById('sheetStructuredChips');
        const priorAuthEl = document.getElementById('sheetPriorAuthBadge');
        const sheetFullText = document.getElementById('sheetFullText');

        if (criteriaSection && chipsContainer) {
            chipsContainer.innerHTML = '';
            const bios = reg.conditions_of_payment.structured_biomarkers || [];
            const steps = reg.conditions_of_payment.step_therapy || [];
            const stops = reg.conditions_of_payment.stopping_rules || [];
            const evals = reg.conditions_of_payment.evaluation_intervals || [];
            const priorAuth = reg.conditions_of_payment.prior_authorization_required;
            const priorAuthGrounding = reg.conditions_of_payment.prior_authorization_grounding;

            if (priorAuth && priorAuthEl) {
                priorAuthEl.innerHTML = `<span class="badge-prior-auth" style="cursor:pointer;"><i class="fa-solid fa-stamp"></i> 事前審查</span>`;
                const paMatch = priorAuthGrounding ? (priorAuthGrounding.snippet || priorAuthGrounding.matched_text || '') : '事前審查';
                priorAuthEl.onclick = () => scrollToMobileHighlight(reg.reference_annotations.full_text, paMatch);
            } else if (priorAuthEl) {
                priorAuthEl.innerHTML = '';
            }

            const chipStyle = 'background:rgba(30,41,59,0.9); border:1px solid rgba(56,189,248,0.3); border-radius:6px; padding:0.25rem 0.55rem; font-size:0.75rem; color:#e2e8f0; cursor:pointer;';
            if (bios.length > 0 || steps.length > 0 || stops.length > 0 || evals.length > 0 || priorAuth) {
                criteriaSection.classList.remove('hidden');

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
                    chip.style.cssText = chipStyle;
                    const countBadge = b.snippets.length > 1 ? ` <span style="opacity:0.75; font-size:0.7rem;">(×${b.snippets.length})</span>` : '';
                    chip.innerHTML = `<i class="fa-solid fa-vial" style="color:#10b981;"></i> <strong>${escapeHtml(b.biomarker)}</strong> ${escapeHtml(b.operator === 'status' ? '' : b.operator)} ${escapeHtml(String(b.value))}${b.unit ? ' ' + escapeHtml(b.unit) : ''}${countBadge}`;
                    chip.addEventListener('click', () => {
                        if (b.snippets.length > 0) {
                            const idx = b.clickIdx % b.snippets.length;
                            const targetSnippet = b.snippets[idx];
                            let sameSnippetOcc = 0;
                            for (let i = 0; i < idx; i++) {
                                if (b.snippets[i] === targetSnippet) sameSnippetOcc++;
                            }
                            b.clickIdx++;
                            scrollToMobileHighlight(reg.reference_annotations.full_text, targetSnippet, sameSnippetOcc);
                        }
                    });
                    chipsContainer.appendChild(chip);
                });

                evals.forEach((ev) => {
                    const chip = document.createElement('button');
                    chip.style.cssText = chipStyle;
                    const evLabel = typeof ev === 'string' ? ev : (ev.schedule || ev.frequency || '');
                    const evSnippet = typeof ev === 'string' ? ev : (ev.source_grounding ? (ev.source_grounding.snippet || ev.source_grounding.matched_text) : evLabel);
                    chip.innerHTML = `<i class="fa-regular fa-clock" style="color:#38bdf8;"></i> 評估/續用: ${escapeHtml(evLabel)}`;
                    chip.addEventListener('click', () => {
                        if (evSnippet) scrollToMobileHighlight(reg.reference_annotations.full_text, evSnippet);
                    });
                    chipsContainer.appendChild(chip);
                });

                steps.slice(0, 3).forEach((st) => {
                    const chip = document.createElement('button');
                    chip.style.cssText = chipStyle;
                    const stLabel = typeof st === 'string' ? st : (st.rule || st.requirement || '');
                    const stSnippet = typeof st === 'string' ? st : (st.source_grounding ? (st.source_grounding.snippet || st.source_grounding.matched_text) : stLabel);
                    const shortRule = stLabel.length > 22 ? stLabel.substring(0, 22) + '...' : stLabel;
                    chip.innerHTML = `<i class="fa-solid fa-stairs" style="color:#f59e0b;"></i> 二線/轉換: ${escapeHtml(shortRule)}`;
                    chip.addEventListener('click', () => {
                        if (stSnippet) scrollToMobileHighlight(reg.reference_annotations.full_text, stSnippet);
                    });
                    chipsContainer.appendChild(chip);
                });

                stops.slice(0, 3).forEach((sp) => {
                    const chip = document.createElement('button');
                    chip.style.cssText = chipStyle;
                    const spLabel = typeof sp === 'string' ? sp : (sp.rule || sp.condition || '');
                    const spSnippet = typeof sp === 'string' ? sp : (sp.source_grounding ? (sp.source_grounding.snippet || sp.source_grounding.matched_text) : spLabel);
                    const shortRule = spLabel.length > 22 ? spLabel.substring(0, 22) + '...' : spLabel;
                    chip.innerHTML = `<i class="fa-solid fa-ban" style="color:#ef4444;"></i> 停藥/排除: ${escapeHtml(shortRule)}`;
                    chip.addEventListener('click', () => {
                        if (spSnippet) scrollToMobileHighlight(reg.reference_annotations.full_text, spSnippet);
                    });
                    chipsContainer.appendChild(chip);
                });
            } else {
                criteriaSection.classList.add('hidden');
            }
        }

        const rawSegments = mobileSearchInput.value.trim().split(/[,，;；]+/).map(s => s.trim()).filter(s => s.length >= 2);
        const activeHighlights = (mobileSearchInput.value.trim() && currentHighlightTerms.length > 0) ? currentHighlightTerms : rawSegments;
        renderFormattedText(sheetFullText, reg.reference_annotations.full_text, activeHighlights.length > 0 ? activeHighlights : null);

        mobileDetailSheet.classList.remove('hidden');

        if (activeHighlights.length > 0) {
            setTimeout(() => {
                const targetEl = sheetFullText.querySelector('.clause-header-matched') || sheetFullText.querySelector('.grounding-highlight');
                if (targetEl) targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 80);
        }
    }

    function scrollToMobileHighlight(fullText, highlightSnippet, occurrenceIdx = 0) {
        const sheetFullText = document.getElementById('sheetFullText');
        renderFormattedText(sheetFullText, fullText, highlightSnippet);
        setTimeout(() => {
            const marks = sheetFullText.querySelectorAll('.grounding-highlight');
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
                        const anchorId = `m-clause-sec-${cNum}-${lineIdx}`;
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
                    <span class="clause-jump-label"><i class="fa-solid fa-compass"></i> 條文段落快速跳轉：</span>
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
                    if (regex) s = s.replace(regex, `<mark class="grounding-highlight">$1</mark>`);
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
