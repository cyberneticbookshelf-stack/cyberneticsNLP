# Topic re-validation sheet — run 20260920-2 (575 books, k=9, seeds 5)

New equivalence class. Topic positions do **not** carry over from `run_20260719_k9_s5` (566 books):
two pairs of July topics merged, one split, one dispersed.

## Settled — transfers confirmed

- **T2** — Social Systems and Second-Order Constructivism  <sub>(July T5, 9/10 of its top-10 books)</sub>
- **T3** — Management and Organisational Cybernetics  <sub>(July T7, 10/10 of its top-10 books)</sub>
- **T4** — Biological and Ecological Regulation: Homeostasis & Allostasis  <sub>(July T3, 10/10 of its top-10 books)</sub>
- **T1** — *unnamed residual* — retained in the k=9 solution, excluded from interpretation and
  reporting. **Not a dead topic:** `dead_topic()` returns False (top-10 loadings 1.00, 0.99,
  0.76, 0.63, 0.61, …), so the zero-dead-topics basis for canonical k=9 in
  `docs/decisions.md` §"Dead-topic count" is unaffected. Dropped on incoherence between its
  word list (Sinophone) and its book list (3 of 7 have no China content), at 0.159 stability
  and 7 books — the residue of July T2's dispersal.

## Reporting framing — decided

Reports and shared HTML describe the solution as **"nine topics, one residual"** — the k=9
model is stated as fitted, with T1 named as a residual rather than silently omitted. Reader-facing
counts are therefore 9 topics / 8 interpreted. This keeps the k=9 provenance legible and
avoids implying an 8-topic model was fitted.

## Open — name these five

Name each as a **discursive register** ("how cybernetics gets written about"), not a subject
domain. July provenance is evidence of where the cluster came from, not a name proposal.


---

## T1  ·  stability 0.159 (moderate)  ·  dominant for 7 books  ·  RESOLVED: unnamed residual

Median loading 0.63 · 5 books at ≥0.50 · years 1970–2026, median 2016

**NAME:** — *(none; retained as residual, excluded from interpretation)*

**NOTES:** Evidence retained below for the record.

**Distinctive words** (in no other topic's top 20): city, qian, chinese, water, xuesen, ancient, china, century, invention, tion

**Shared words:** culture, technology

**July provenance** — of each July topic's top-10 books, how many are now here:

- **3/10 from July T2** *"Extensions and Exploration of Cybernetics"* — voice, sound, music, qian, chinese, china, opera, object
    - [2771] A Cybernetic Study of Speaking and Singing
    - [2733] The Question Concerning Technology in China: An Essay in Cosmo
    - [2333] Return to China One Day: The Learning Life of Qian Xuesen

**Top 20 loadings now:**

- `1.000` [2771] *A Cybernetic Study of Speaking and Singing* — Jon Piso (2017)
- `0.993` [2825] *The Shan-Shui City: Cybernetics, Cosmos, and the Future of Urban E* — Fengchen & Chang, Liang He (2026)
- `0.756` [2333] *Return to China One Day: The Learning Life of Qian Xuesen* — Chengdong Lv (2023)
- `0.630` [2733] *The Question Concerning Technology in China: An Essay in Cosmotech* — Yuk Hui (2016)
- `0.609` [2638] *Cybernetics Within Us* — Elena V. Saparina (1982)
- `0.405` [2731] *The Origins of Feedback Control* — Otto Mayr (1970)
- `0.365` [2271] *Cybernetic Principles of Learning and Educational Design* — Karl Ulrich & Smith, Marga (1966)
- `0.348` [2115] *Introduction to the History of Communication: Evolutions & Revolut* — Terence P. Moran (2010)
- `0.295` [2252] *The Death of Jeffrey Stapleton: Exploring the Way Lawyers Think* — Hugh Gibbons (2013)
- `0.291` [2318] *Gods and Robots: Myths, Machines, and Ancient Dreams of Technology* — Adrienne Mayor (2018)
- `0.181` [2186] *Balinese Character: A Photographic Analysis* — Gregory & Mead, Margaret B (1942)
- `0.156` [2517] *Invention: The Care and Feeding of Ideas* — Norbert Wiener (1994)
- `0.118` [2726] *The Human Use of Human Beings: Cybernetics and Society* — Norbert Wiener (1989)
- `0.108` [2117] *Understanding Me: Lectures and Interviews* — Marshall McLuhan (2005)
- `0.106` [2146] *Subduing the Cosmos: Cybernetics and Man's Future* — Kenneth L. Vaux (1970)
- `0.102` [2725] *The Information: A History, a Theory, a Flood* — James Gleick (2011)
- `0.092` [2516] *Pebbles to Computers: The Thread* — Hans & Beer, Stafford & Su (1986)
- `0.091` [2165] *Cybernetic Aspects of Language* — W. W. Schuhmacher (1972)
- `0.088` [2222] *The Freudian Robot: Digital Media and the Future of the Unconsciou* — Lydia H. Liu (2011)
- `0.068` [2068] *Communication Theory Through the Ages* — Igor & Sinekopova, Galina  (2019)


---

## T5  ·  stability 0.320 (stable)  ·  dominant for 45 books

Median loading 0.55 · 28 books at ≥0.50 · years 1967–2025, median 2018

**NAME:** ________________________________________________

**NOTES:**

**Distinctive words** (in no other topic's top 20): medium, artist, digital, robot, program

**Shared words:** computer, machine, technology, cybernetic, body, image, object

**July provenance** — of each July topic's top-10 books, how many are now here:

- **4/10 from July T2** *"Extensions and Exploration of Cybernetics"* — voice, sound, music, qian, chinese, china, opera, object
    - [2281] Cybernetic Avatar
    - [2091] Machine Sensation: Anthropomorphism and 'Natural' Interaction 
    - [2046] Embodiment of the Everyday Cyborg: Technologies of the Altered
    - [2772] Sonic Intimacy: Voice, Species, Technics (Or, How to Listen to
- **4/10 from July T9** *"Digital Arts, Architecture, Design and Posthumanism"* — technology, cybernetic, machine, social, medium, digital, 
    - [2089] Posthumanism and the Graphic Novel in Latin America
    - [2218] Telematic Embrace: Visionary Theories of Art, Technology, and 
    - [2448] Digital Performance: A History of New Media in Theater, Dance,
    - [2198] Twins and Recursion in Digital, Literary and Visual Cultures
- **2/10 from July T1** *"History of Information Age and Cybernetics"* — machine, computer, wiener, century, technology, american, 
    - [2730] The Media Lab: Inventing the Future at MIT
    - [2685] Our Robots, Ourselves: Robotics and the Myths of Autonomy

**Top 20 loadings now:**

- `0.884` [2047] *The Composer's Black Box: Making Music in Cybernetic America* — Theodore Gordon (2025)
- `0.866` [2448] *Digital Performance: A History of New Media in Theater, Dance, Per* — Steve Dixon (2007)
- `0.858` [2657] *History of Computer Art* — Thomas Dreher (2020)
- `0.852` [2398] *Cybernethisms: Aldo Giorgini's Computer Art Legacy* — Esteban García Bravo (2015)
- `0.789` [2351] *Northern Sparks: Innovation, Technology Policy, and the Arts in Ca* — Michael Century (2022)
- `0.769` [2078] *Experimenting the Human: Art, Music, and the Contemporary Posthuma* — G Douglas Barrett (2023)
- `0.765` [2088] *Behaviourist Art and Cybernetics: Mapping a Field* — Kate Sloan (2025)
- `0.761` [2349] *Art + DIY Electronics* — Garnet Hertz (2023)
- `0.738` [2095] *Cyborgs in Latin America* — J. Brown (2010)
- `0.735` [2492] *Confronting the Machine: An Enquiry Into the Subversive Drives of * — Boris Magrini (2017)
- `0.713` [2218] *Telematic Embrace: Visionary Theories of Art, Technology, and Cons* — Roy Ascott (2003)
- `0.700` [2227] *Machine Art in the Twentieth Century* — Andreas Broeckmann (2016)
- `0.694` [2590] *Art, Cybernetics and Pedagogy in Post-War Britain: Roy Ascott's Gr* — Kate Sloan (2019)
- `0.690` [2091] *Machine Sensation: Anthropomorphism and 'Natural' Interaction With* — Tessa Leach (2020)
- `0.685` [2264] *Relational Improvisation: Music, Dance and Contemporary Art* — Simon Rose (2024)
- `0.652` [2073] *Sensing and Making Sense: Photosensitivity and Light-To-Sound Tran* — Graziele Lautenschlaeger (2021)
- `0.637` [2198] *Twins and Recursion in Digital, Literary and Visual Cultures* — Edward King (2022)
- `0.613` [2601] *Cinema, Trance and Cybernetics* — Ute Holl (2017)
- `0.609` [2205] *Brainmedia: One Hundred Years of Performing Live Brains, 1920–2020* — Flora Lysen (2022)
- `0.598` [2281] *Cybernetic Avatar* — Hiroshi & Ueno, Fuki & Tac (2024)


---

## T6  ·  stability 0.413 (stable)  ·  dominant for 59 books

Median loading 0.70 · 46 books at ≥0.50 · years 1954–2025, median 2002

**NAME:** ________________________________________________

**NOTES:**

**Distinctive words** (in no other topic's top 20): input, variable, equation, output, rate, define, property, probability

**Shared words:** feedback, network, energy, signal

**July provenance** — of each July topic's top-10 books, how many are now here:

- **10/10 from July T6** *"Foundations of Cybernetics"* — define, entropy, probability, theorem, equation, shall, in
    - [2670] Mathematical Structure of Finite Random Cybernetic Systems: Le
    - [2097] The Mathematical Theory of Semantic Communication
    - [2700] Reflexion and Control: Mathematical Models
    - [2127] Wholes and Parts: A General Theory of System Behaviour
- **8/10 from July T8** *"Control and Feedback Systems"* — input, machine, feedback, variable, output, signal, behavi
    - [2678] Neural Networks as Cybernetic Systems
    - [2451] Neural Network Modeling: Statistical Mechanics and Cybernetic 
    - [2750] Marine Control Systems: Guidance, Navigation and Control of Sh
    - [2356] Engineering Cybernetics

**Top 20 loadings now:**

- `1.000` [2750] *Marine Control Systems: Guidance, Navigation and Control of Ships,* — Thor I. Fossen (2002)
- `1.000` [2356] *Engineering Cybernetics* — Qian Xuesen (1954)
- `1.000` [2418] *Cybernetical Physics: From Control of Chaos to Quantum Control* — A. Fradkov (2007)
- `1.000` [2145] *Random Wavelets and Cybernetic Systems* — Endrs A Robinson (1962)
- `1.000` [2670] *Mathematical Structure of Finite Random Cybernetic Systems: Lectur* — Silviu Guiasu (1972)
- `0.993` [2097] *The Mathematical Theory of Semantic Communication* — Kai & Zhang, Ping Niu (2025)
- `0.993` [2194] *Biological Feedback* — Rene & D'Ari, Richard Thom (1990)
- `0.966` [2388] *Generalized Harmonic Analysis and Tauberian Theory, Classical Harm* — Norbert Wiener (1976)
- `0.966` [2127] *Wholes and Parts: A General Theory of System Behaviour* — Oskar Lange (1965)
- `0.953` [2678] *Neural Networks as Cybernetic Systems* — Holk Cruse (1996)
- `0.944` [2744] *Cybernetic Modeling for Bioreaction Engineering* — Doraiswami & Song, Hyun-Se (2018)
- `0.940` [2387] *The Hopf-Wiener Integral Equation: Prediction and Filtering ; Quan* — Norbert Wiener (1981)
- `0.931` [2206] *Application of New Cybernetics in Physics* — Oleg Kupervasser (2017)
- `0.910` [2695] *Quantum Cybernetics: Toward a Unification of Relativity and Quantu* — Gerhard Grössing (2000)
- `0.902` [2700] *Reflexion and Control: Mathematical Models* — Dmitry A. & Chkhartishvili (2014)
- `0.900` [2671] *Introduction to Economic Cybernetics* — Oskar Lange (1970)
- `0.852` [2809] *Toward a General Science of Viable Systems* — Arthur S. Iberall (1971)
- `0.846` [2328] *Fundamentals of Cybernetics* — A. Ya. Lerner (2012)
- `0.827` [2291] *The Cybernetic Theory of Development Mathematical Models for A Re-* — Y. Agnavaara (1974)
- `0.819` [2435] *Relative Information: Theories and Applications* — Guy Jumarie (2011)


---

## T7  ·  stability 0.334 (stable)  ·  dominant for 81 books

Median loading 0.58 · 46 books at ≥0.50 · years 1942–2025, median 2007

**NAME:** ________________________________________________

**NOTES:**

**Distinctive words** (in no other topic's top 20): bateson, person, feel, family, child, tell, story, therapy, woman, talk, therapist

**Shared words:** image

**July provenance** — of each July topic's top-10 books, how many are now here:

- **10/10 from July T4** *"Cybernetics of Self"* — person, feel, bateson, child, family, behavior, goal, tell
    - [2768] Psycho-Cybernetics and Self-Fulfillment
    - [2522] Freedom From Stress: Most People Deal With Symptoms--This Book
    - [2136] Volleyball Cybernetics
    - [2087] Psycho-Cybernetics 365: Thrive and Grow Every Day of the Year
- **6/10 from July T1** *"History of Information Age and Cybernetics"* — machine, computer, wiener, century, technology, american, 
    - [2279] Whole Earth: The Many Lives of Stewart Brand
    - [2725] The Information: A History, a Theory, a Flood
    - [2637] Dark Hero of the Information Age: In Search of Norbert Wiener,
    - [2318] Gods and Robots: Myths, Machines, and Ancient Dreams of Techno

**Top 20 loadings now:**

- `0.995` [2703] *R.U.R. (Rossum's Universal Robots)* — Karel Capek (2004)
- `0.989` [2768] *Psycho-Cybernetics and Self-Fulfillment* — Maxwell Maltz (2013)
- `0.979` [2560] *@Heaven: The Online Death of a Cybernetic Futurist* — Thomas Mandel (2015)
- `0.975` [2087] *Psycho-Cybernetics 365: Thrive and Grow Every Day of the Year* — Maxwell & Furey, Matthew M (2025)
- `0.965` [2467] *The Cyberiad; Fables for the Cybernetic Age* — Stanisław Lem (1974)
- `0.956` [2764] *The Cyberiad: Stories* — Stanisław Lem (2002)
- `0.956` [2136] *Volleyball Cybernetics* — Stan & Cross, Dave Kellner (1998)
- `0.929` [2297] *With a Daughter's Eye: A Memoir of Margaret Mead and Gregory Bates* — Mary Catherine Bateson (1984)
- `0.912` [2565] *Psycho-Cybernetics: Updated and Expanded* — Maxwell Maltz (2015)
- `0.912` [2303] *Hypno Cybernetics: Helping Yourself to a Rich New Life* — Sidney & Stone, Robert B.  (1976)
- `0.911` [2696] *Psycho-Cybernetics* — Maxwell Maltz (1969)
- `0.904` [2114] *Sexual Cybernetics* — Paul J. Gillette (1973)
- `0.897` [2298] *Full Circles Overlapping Lives: Culture and Generation in Transiti* — Mary Catherine Bateson (2000)
- `0.883` [2709] *Success Cybernetics (Unabridged Edition)* — Uell S. Andersen (2022)
- `0.869` [2677] *Norbert Wiener-A Life in Cybernetics: Ex-Prodigy: My Childhood and* — Norbert & Kline, Ronald R. (2018)
- `0.865` [2482] *The Cybernetics of Prejudices in the Practice of Psychotherapy* — Gianfranco & Lane, Gerry & (1994)
- `0.864` [2522] *Freedom From Stress: Most People Deal With Symptoms--This Book, Ba* — Edward E. Ford (1989)
- `0.863` [2345] *The Creative Therapist in Practice* — Hillary & Keeney, Bradford (2019)
- `0.855` [2439] *Gregory Bateson: The Legacy of a Scientist* — David Lipset (1982)
- `0.842` [2184] *Composing a Life* — Mary Catherine Bateson (2007)


---

## T8  ·  stability 0.455 (stable)  ·  dominant for 67 books

Median loading 0.53 · 40 books at ≥0.50 · years 1970–2025, median 2017

**NAME:** ________________________________________________

**NOTES:**

**Distinctive words** (in no other topic's top 20): wiener, political, economic, architecture

**Shared words:** cybernetic, social, technology, society, machine, culture, computer, network

**July provenance** — of each July topic's top-10 books, how many are now here:

- **6/10 from July T9** *"Digital Arts, Architecture, Design and Posthumanism"* — technology, cybernetic, machine, social, medium, digital, 
    - [2204] Architecture in Digital Culture: Machines, Networks and Comput
    - [2591] Architectural Principles in the Age of Cybernetics
    - [2225] With and Against: The Situationist International in the Age of
    - [2059] Concrete Encoded: Poetry, Design, and the Cybernetic Imaginary
- **1/10 from July T1** *"History of Information Age and Cybernetics"* — machine, computer, wiener, century, technology, american, 
    - [2099] Machines of Loving Grace: The Quest for Common Ground Between 
- **1/10 from July T2** *"Extensions and Exploration of Cybernetics"* — voice, sound, music, qian, chinese, china, opera, object
    - [2085] Anime's Knowledge Cultures: Geek, Otaku, Zhai

**Top 20 loadings now:**

- `0.918` [2331] *The Cybernetic Border: Drones, Technology, and Intrusion* — Iván Chaar López (2024)
- `0.904` [2569] *The Internet Revolution: From Dot-Com Capitalism to Cybernetic Com* — Richard & Cameron, Andy Ba (2015)
- `0.904` [2449] *Imaginary Futures: From Thinking Machines to the Global Village* — Richard Barbrook (2007)
- `0.902` [2607] *Constructing Soviet Cultural Policy: Cybernetics and Governance in* — Eglė Rindzevičiūtė (2008)
- `0.854` [2567] *The Opening of the Cybernetic Frontier: Cities of the Prairie* — Daniel Elazar (2018)
- `0.853` [2352] *Balkan Cyberia: Cold War Computing, Bulgarian Modernization, and t* — Victor Petrov (2023)
- `0.844` [2379] *The Power of Systems: How Policy Sciences Opened Up the Cold War W* — Eglė Rindzevičiūtė (2016)
- `0.822` [2305] *The Informational Logic of Human Rights: Network Imaginaries in th* — Joshua Bowsher (2022)
- `0.822` [2294] *Border Security: Shores of Politics, Horizons of Justice* — Peter Chambers (2017)
- `0.818` [2661] *How Not to Network a Nation: The Uneasy History of the Soviet Inte* — Benjamin Peters (2016)
- `0.806` [2224] *Climatic Media: Transpacific Experiments in Atmospheric Control* — Yuriko Furuhata (2022)
- `0.796` [2269] *Cybernetic Circulation Complex: Big Tech and Planetary Crisis* — Nick & Mularoni, Alessandr (2025)
- `0.743` [2225] *With and Against: The Situationist International in the Age of Aut* — Dominique Routhier (2023)
- `0.732` [2090] *The Dark Posthuman: Dehumanization, Technology, and the Atlantic W* — Stephanie Polsky (2022)
- `0.728` [2200] *Last Futures: Nature, Technology and the End of Architecture* — Douglas Murphy (2022)
- `0.717` [2267] *Cyber-Proletariat: Global Labour in the Digital Vortex* — Nick Dyer-Witheford (2015)
- `0.713` [2634] *Cybernetics, Warfare and Discourse: The Cybernetisation of Warfare* — Anthimos Alexandros Tsirig (2017)
- `0.700` [2085] *Anime's Knowledge Cultures: Geek, Otaku, Zhai* — Jinying Li (2024)
- `0.698` [2599] *Code: From Information Theory to French Theory* — Bernard Dionysius Geoghega (2023)
- `0.696` [2278] *Think Tank Aesthetics: Midcentury Modernism, the Cold War, and the* — Pamela M. Lee (2020)


---

## T9  ·  stability 0.237 (moderate)  ·  dominant for 110 books

Median loading 0.53 · 68 books at ≥0.50 · years 1954–2025, median 1991

**NAME:** ________________________________________________

**NOTES:**

**Distinctive words** (in no other topic's top 20): perception, pattern, message

**Shared words:** machine, behavior, language, brain, computer, cybernetic, organism, object, signal

**July provenance** — of each July topic's top-10 books, how many are now here:

- **1/10 from July T1** *"History of Information Age and Cybernetics"* — machine, computer, wiener, century, technology, american, 
    - [2378] The Dream Machine
- **1/10 from July T5** *"Social Systems and Second-Order Constructivism"* — social, communication, language, meaning, object, distinct
    - [2253] The Dilemma of Enquiry and Learning
- **1/10 from July T8** *"Control and Feedback Systems"* — input, machine, feedback, variable, output, signal, behavi
    - [2737] The Study of Living Control Systems: A Guide to Doing Research

**Top 20 loadings now:**

- `0.988` [2690] *Philosophical Foundations of Cybernetics* — Frank Honywill George (1979)
- `0.953` [2721] *The Discovery of the Artificial: Behavior, Mind and Machines Befor* — R. Cordeschi (2010)
- `0.923` [2479] *Purposive Explanation in Psychology* — Margaret A. Boden (2013)
- `0.919` [2151] *Cybernetics and Biology* — Frank Honywill George (1965)
- `0.907` [2235] *The Foundations of Cybernetics* — Frank Honywill George (1977)
- `0.896` [2158] *Cybernetics* — Frank Honywill George (1971)
- `0.876` [2055] *Instructional Regulation and Control: Cybernetics, Algorithmizatio* — Lev Nakhmanovich Landa (1976)
- `0.852` [2376] *Artificial Intelligence: Its Philosophy and Neural Context* — Frank Honywill George (2018)
- `0.844` [2716] *The Cybernetic Foundation Mathematics* — Valentin Fedorovich Turchi (1983)
- `0.828` [2315] *Information, Mechanism and Meaning* — Donald MacCrimmon MacKay (1969)
- `0.813` [2616] *Conversation Theory: Applications in Education and Epistemology* — Gordon Pask (1976)
- `0.808` [2240] *Philosophy and Cybernetics* — Frederick J & Sayre, Kenne (1967)
- `0.806` [2614] *Conversation, Cognition and Learning: A Cybernetic Theory and Meth* — Gordon Pask (1975)
- `0.802` [2808] *Systems Theory and Scientific Philosophy: An Application of the Cy* — John Bryant (1991)
- `0.761` [2754] *The Cybernetics of Human Learning and Performance* — Gordon Pask (1975)
- `0.758` [2102] *Minds and Machines* — W. Sluckin (1954)
- `0.758` [2393] *The Computer and the Brain* — John von & Kurzweil, Ray N (1957)
- `0.756` [2126] *Automation, Cybernetics, and Society* — Frank Honywill George (1959)
- `0.751` [2154] *Cybernetics in Management* — Frank Honywill George (1970)
- `0.746` [2627] *Cybernetics and Development: International Series of Monographs in* — Michael J. Apter (2016)


---

## Caveat

Single-rater naming on a single run. Sprint item 4 (≥3 runs × ≥2 raters)
remains outstanding; whatever is chosen here is provisional.
