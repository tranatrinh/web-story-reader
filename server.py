    <script>
        const fileInput = document.getElementById('fileInput'); 
        const storyText = document.getElementById('storyText'); 
        const status = document.getElementById('status'); 
        const chapterSelect = document.getElementById('chapterSelect');
        const speedSelect = document.getElementById('speedSelect');

        let chapters = [];
        let currentChapterIndex = 0;

        // --- ĐỌC VÀ TÁCH CHƯƠNG FILE ---
        fileInput.addEventListener('change', async (e) => { 
            const file = e.target.files[0]; 
            if (!file) return; 
            status.textContent = `⏳ Đang phân tích file: ${file.name}...`; 
            storyText.value = ""; 
            chapters = [];
            chapterSelect.style.display = "none";
            chapterSelect.innerHTML = "";

            try { 
                if (file.name.toLowerCase().endsWith('.txt')) { 
                    const text = await file.text(); 
                    const splits = text.split(/^(?=Chương\s+\d+|Hồi\s+\d+|Quyển\s+\d+)/im);
                    if (splits.length <= 1) {
                        chapters.push({ title: "Toàn bộ nội dung", content: text });
                    } else {
                        splits.forEach((content) => {
                            if (content.trim()) {
                                let title = content.trim().split('\n')[0].substring(0, 40) + "...";
                                chapters.push({ title: title, content: content.trim() });
                            }
                        });
                    }
                } else if (file.name.toLowerCase().endsWith('.epub')) { 
                    const zip = await JSZip.loadAsync(file); 
                    const containerXml = await zip.file("META-INF/container.xml").async("text"); 
                    const parser = new DOMParser(); 
                    const containerDoc = parser.parseFromString(containerXml, "text/xml"); 
                    const opfPath = containerDoc.querySelector("rootfile").getAttribute("full-path"); 
                    const basePath = opfPath.substring(0, opfPath.lastIndexOf('/') + 1); 
                    const opfXml = await zip.file(opfPath).async("text"); 
                    const opfDoc = parser.parseFromString(opfXml, "text/xml"); 
                    
                    const manifest = {}; 
                    opfDoc.querySelectorAll("manifest > item").forEach(item => { 
                        manifest[item.getAttribute("id")] = item.getAttribute("href"); 
                    }); 
                    const spineItems = opfDoc.querySelectorAll("spine > itemref"); 
                    
                    for (let i = 0; i < spineItems.length; i++) { 
                        const idref = spineItems[i].getAttribute("idref"); 
                        const href = manifest[idref]; 
                        if (href) { 
                            const filePath = basePath + decodeURIComponent(href); 
                            const fileInZip = zip.file(filePath); 
                            if (fileInZip) { 
                                const htmlContent = await fileInZip.async("text"); 
                                const htmlDoc = parser.parseFromString(htmlContent, "text/html"); 
                                const titleTag = htmlDoc.querySelector("title");
                                const title = titleTag && titleTag.textContent ? titleTag.textContent.trim() : `Phần ${i + 1}`;
                                const text = htmlDoc.body.textContent || htmlDoc.body.innerText; 
                                if(text.trim()) {
                                    chapters.push({ title: title, content: text.trim() });
                                }
                            } 
                        } 
                    } 
                }
                
                chapters.forEach((chap, idx) => {
                    const opt = document.createElement("option");
                    opt.value = idx;
                    opt.textContent = chap.title;
                    chapterSelect.appendChild(opt);
                });
                chapterSelect.style.display = "block";
                chapterSelect.value = 0;
                loadSelectedChapter();
                status.textContent = `✅ Đã tải xong ${chapters.length} chương!`; 
            } catch (err) { 
                status.textContent = `❌ Lỗi đọc file.`; 
            } 
        }); 

        function loadSelectedChapter() {
            currentChapterIndex = parseInt(chapterSelect.value);
            if(chapters[currentChapterIndex]) {
                storyText.value = chapters[currentChapterIndex].content;
                storyText.scrollTop = 0;
            }
        }

        // --- HỆ THỐNG PHÁT AUDIO TỐI ƯU CHỐNG QUÁ TẢI RENDER ---
        let globalAudio = new Audio();
        let isPlaying = false;
        let chunks = [];
        let currentChunkIndex = 0;

        function splitTextForAPI(text) {
            const cleanText = text.replace(/[\r\n]+/g, " ").trim();
            const sentences = cleanText.match(/[^.!?]+[.!?]+(\s|$)/g) || [cleanText];
            
            const result = [];
            let currentChunk = "";

            sentences.forEach(sentence => {
                // Tăng độ dài mỗi chunk lên ~500 ký tự để giảm số lượng request gửi lên Render
                if ((currentChunk + sentence).length > 500) {
                    if (currentChunk) result.push(currentChunk.trim());
                    currentChunk = sentence;
                } else {
                    currentChunk += sentence;
                }
            });
            if (currentChunk) result.push(currentChunk.trim());
            return result.filter(ch => ch.length > 0);
        }

        async function getAudioBlob(text, retries = 4) {
            for (let i = 0; i < retries; i++) {
                try {
                    const response = await fetch("https://story-reader-api.onrender.com/tts", {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'Accept': 'audio/mp3'
                        },
                        body: JSON.stringify({ text: text })
                    });
                    
                    if (!response.ok) {
                        throw new Error("Server bận");
                    }
                    
                    const blob = await response.blob();
                    return URL.createObjectURL(blob);
                } catch (err) {
                    if (i === retries - 1) throw err;
                    // Chờ lâu hơn giữa các lần thử lại (3 giây) để server Render hồi phục CPU
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }
            }
        }

        function updateSpeed() {
            if (globalAudio) {
                globalAudio.playbackRate = parseFloat(speedSelect.value);
            }
        }

        async function startTTS() { 
            const text = storyText.value.trim(); 
            if (!text) { alert("Không có nội dung để đọc!"); return; } 

            chunks = splitTextForAPI(text); 
            if (chunks.length === 0) { alert("Văn bản không hợp lệ!"); return; }

            currentChunkIndex = 0;
            isPlaying = true;
            
            // Mở khóa audio trên iOS Safari
            globalAudio.src = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA";
            await globalAudio.play().catch(() => {});

            playSequence();
        } 

        async function playSequence() {
            let nextAudioPromise = null;

            while (isPlaying && currentChunkIndex < chunks.length) {
                try {
                    let currentUrl;
                    
                    if (nextAudioPromise) {
                        status.textContent = `🔊 Đang chuẩn bị đoạn ${currentChunkIndex + 1}/${chunks.length}...`;
                        currentUrl = await nextAudioPromise;
                        nextAudioPromise = null;
                    } else {
                        status.textContent = `⏳ Đang tải đoạn ${currentChunkIndex + 1}/${chunks.length}...`;
                        currentUrl = await getAudioBlob(chunks[currentChunkIndex]);
                    }
                    
                    if (!isPlaying) {
                        URL.revokeObjectURL(currentUrl);
                        break;
                    }

                    // Tăng độ trễ gối đầu lên 2 giây để Render không bị dồn dập request
                    if (currentChunkIndex + 1 < chunks.length) {
                        await new Promise(resolve => setTimeout(resolve, 2000)); 
                        nextAudioPromise = getAudioBlob(chunks[currentChunkIndex + 1]);
                    }

                    globalAudio.src = currentUrl;
                    globalAudio.playbackRate = parseFloat(speedSelect.value);
                    status.textContent = `🔊 Đang đọc: ${chapters[currentChapterIndex].title} (Đoạn ${currentChunkIndex + 1}/${chunks.length})`;
                    
                    await new Promise((resolve, reject) => {
                        globalAudio.onended = resolve;
                        globalAudio.onerror = (e) => reject(new Error("Lỗi phát audio"));
                        globalAudio.play().catch(reject);
                    });

                    URL.revokeObjectURL(currentUrl);
                    currentChunkIndex++;

                } catch (err) {
                    status.textContent = `⚠️ Quá tải, đang kết nối lại...`;
                    await new Promise(resolve => setTimeout(resolve, 4000));
                }
            }

            if (isPlaying && currentChunkIndex >= chunks.length) {
                if (currentChapterIndex < chapters.length - 1) {
                    status.textContent = "⏭ Đang chuyển chương tiếp theo...";
                    currentChapterIndex++;
                    chapterSelect.value = currentChapterIndex;
                    loadSelectedChapter();
                    setTimeout(() => { if (isPlaying) startTTS(); }, 2000);
                } else {
                    status.textContent = "✅ Đã đọc hết truyện.";
                    isPlaying = false;
                }
            }
        }

        function stopTTS() { 
            isPlaying = false;
            globalAudio.pause();
            globalAudio.src = "";
            status.textContent = "⏹ Đã dừng đọc."; 
        }
    </script>
