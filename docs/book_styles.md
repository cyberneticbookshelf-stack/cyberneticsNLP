# Book Style Classification

**Date:** 2026-04-10  
**Corpus:** 714 books  
**Input:** csv/books_metadata_full.csv  
**Method:** Heuristic signal matching — title, author, publisher, description, tags  

## Summary

| Style | Count | % |
|---|---|---|
| monograph | 546 | 76.5% |
| anthology | 38 | 5.3% |
| textbook | 38 | 5.3% |
| popular | 38 | 5.3% |
| history_bio | 28 | 3.9% |
| handbook | 13 | 1.8% |
| proceedings | 7 | 1.0% |
| reader | 5 | 0.7% |
| report | 1 | 0.1% |

## Inclusion Strata

| Stratum | Count | % |
|---|---|---|
| curated_pure | 315 | 44.1% |
| title_corroborated | 197 | 27.6% |
| curated_keyword | 133 | 18.6% |
| title_only | 55 | 7.7% |
| metadata_search | 14 | 2.0% |

## Epistemic Affordances by Style

| Style | Sampling validity | Index type | LDA signal | Temporal bias |
|---|---|---|---|---|
| Monograph | High | Author's concept map | Clean | None |
| Anthology | Low | Union of contributors | Mixed | Variable |
| Textbook | Medium | Comprehensive, conservative | Smoothed | Retrospective |
| Handbook | Low | Community concept map | Mixed | Retrospective |
| Reader | Low–Medium | Curated canon | Historically weighted | Retrospective |
| Popular | High | Thin or absent | Distinct register | None |
| History/Bio | High | Proper-noun heavy | Historiographic | None |
| Proceedings | Very low | Often absent | Highly mixed | None |
| Report | High | Variable | Variable | None |

## Classification Review Table

Review and correct the `style` column. Set `verified=true` in book_styles.json after checking.

| ID | Title | Year | Publisher | Style | Conf | Stratum | Signals |
|---|---|---|---|---|---|---|---|
| 2545 | Cybernetika 1.0 | 0101 |  | **monograph** | low | curated_pure | default:no_signals |
| 2186 | Balinese Character: A Photographic Analysis | 1942 | New York academy of  | **monograph** | low | curated_pure | default:no_signals |
| 2075 | The Next Step in Management: An Appraisal of  | 1952 |  | **monograph** | low | title_only | default:no_signals |
| 2239 | Cybernetics: Circular, Causal and Feedback Me | 1953 | Macy Foundation | **monograph** | low | title_corroborated | default:no_signals |
| 2104 | The Origins of Life | 1957 | Creative Media Partn | **monograph** | low | curated_keyword | default:no_signals |
| 2393 | The Computer and the Brain | 1957 | Yale University Pres | **monograph** | low | curated_keyword | default:no_signals |
| 2134 | Communication, Organization, and Science | 1958 | Falcon's Wing Press | **monograph** | low | curated_keyword | default:no_signals |
| 2126 | Automation, Cybernetics, and Society | 1959 | L. Hill | **monograph** | low | title_corroborated | default:no_signals |
| 2596 | Cybernetics and Management | 1959 | Wiley | **monograph** | low | title_corroborated | default:no_signals |
| 2761 | What Is Cybernetics? | 1959 | Criterion Books | **monograph** | low | title_only | default:no_signals |
| 2440 | Design for a Brain | 1960 | Springer Netherlands | **monograph** | medium | curated_pure | publisher:springer |
| 2145 | Random Wavelets and Cybernetic Systems | 1962 | CHARLES GRIFFIN & CO | **monograph** | low | title_only | default:no_signals |
| 2100 | Cybernetics | 1963 | Hawthorn Books | **monograph** | low | title_corroborated | default:no_signals |
| 2191 | Nerve, Brain and Memory Models | 1963 | Elsevier | **monograph** | low | curated_pure | default:no_signals |
| 2249 | The Nerves of Government: Models of Political | 1963 | Free Press of Glenco | **monograph** | low | curated_keyword | default:no_signals |
| 2133 | Cybernation and Social Change | 1964 | U.S. Department of L | **monograph** | low | curated_keyword | default:no_signals |
| 2290 | Industrial Dynamics | 1964 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 2116 | Biological Rhythm Research | 1965 | Elsevier Publishing  | **monograph** | low | curated_keyword | default:no_signals |
| 2127 | Wholes and Parts: A General Theory of System  | 1965 | Pergamon Press | **monograph** | low | curated_keyword | default:no_signals |
| 2151 | Cybernetics and Biology | 1965 | W. H. Freeman | **monograph** | low | title_corroborated | default:no_signals |
| 2163 | Cybernetic Medicine | 1965 | C. C. Thomas | **monograph** | low | title_corroborated | default:no_signals |
| 2532 | Embodiments of Mind | 1965 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 2635 | Cybernetics of the Nervous System | 1965 | Elsevier | **monograph** | low | title_corroborated | default:no_signals |
| 2101 | Structure, Form, Movement | 1966 | Reinhold | **monograph** | low | curated_keyword | default:no_signals |
| 2147 | Great Ideas in Information Theory, Language a | 1966 | Dover Publications | **monograph** | low | title_corroborated | default:no_signals |
| 2160 | Cybernetic Modelling | 1966 | Wliffe Books Ltd. | **monograph** | low | title_corroborated | default:no_signals |
| 2265 | Decision and Control: The Meaning of Operatio | 1966 | Wiley | **monograph** | low | title_corroborated | default:no_signals |
| 2563 | God & Golem, Inc.: A Comment on Certain Point | 1966 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2240 | Philosophy and Cybernetics | 1967 | University of Notre  | **monograph** | low | title_corroborated | default:no_signals |
| 2242 | The Science of Art: The Cybernetics of Creati | 1967 | John Day Company | **monograph** | low | title_corroborated | default:no_signals |
| 2306 | Whole Earth Catalog Access to Tools | 1967 |  | **monograph** | low | curated_pure | default:no_signals |
| 2152 | Cybernetics and the Image of Man: A Study of  | 1968 | Abingdon Press | **monograph** | low | title_corroborated | default:no_signals |
| 2157 | Key Papers in Cybernetics | 1968 | University Park Pres | **monograph** | low | title_corroborated | default:no_signals |
| 2272 | Cybernetic Serendipity: The Computer and the  | 1968 | Studio International | **monograph** | low | title_only | default:no_signals |
| 2554 | An Approach to Cybernetics | 1968 | Hutchinson | **monograph** | low | title_corroborated | default:no_signals |
| 2056 | Market Cybernetic Processes | 1969 | Almqvist & Wiksell | **monograph** | low | title_corroborated | default:no_signals |
| 2155 | Cybernetics Simplified | 1969 | English Universities | **monograph** | low | title_corroborated | default:no_signals |
| 2156 | Cybernetics, Society, and the Church | 1969 | Pflaum Press | **monograph** | low | title_corroborated | default:no_signals |
| 2315 | Information, Mechanism and Meaning | 1969 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 2727 | The Management Process, Management Informatio | 1969 | M.I.T. | **monograph** | low | title_corroborated | default:no_signals |
| 2757 | The Social Impact of Cybernetics | 1969 | University of Notre  | **monograph** | low | title_only | default:no_signals |
| 2128 | Kybernetics of Mind and Brain | 1970 | Thomas | **monograph** | low | curated_keyword | default:no_signals |
| 2129 | Politics and Government: How People Decide Th | 1970 | Houghton Mifflin | **monograph** | low | curated_pure | default:no_signals |
| 2135 | The Science of Mental Cybernetics | 1970 | Parker Publishing Co | **monograph** | low | title_only | default:no_signals |
| 2146 | Subduing the Cosmos: Cybernetics and Man's Fu | 1970 | John Knox Press | **monograph** | low | title_corroborated | default:no_signals |
| 2154 | Cybernetics in Management | 1970 | Pan Books | **monograph** | low | title_corroborated | default:no_signals |
| 2384 | You Are a Computer: Cybernetics in Everyday L | 1970 | Emerson Books | **monograph** | low | title_corroborated | default:no_signals |
| 2731 | The Origins of Feedback Control | 1970 | M.I.T. Press | **monograph** | low | curated_keyword | default:no_signals |
| 2062 | The Age of Information: An Interdisciplinary  | 1971 | Educational Technolo | **monograph** | low | title_corroborated | default:no_signals |
| 2158 | Cybernetics | 1971 | St. Paul's House | **monograph** | low | title_corroborated | default:no_signals |
| 2289 | World Dynamics | 1971 | Wright-Allen Press | **monograph** | low | curated_pure | default:no_signals |
| 2354 | Cybernetics, Art, and Ideas | 1971 | Graphie Society | **monograph** | low | title_only | default:no_signals |
| 2505 | The Last Whole Earth Catalog: Access to Tools | 1971 | Portola Institute | **monograph** | low | curated_pure | default:no_signals |
| 2663 | Information and Control in the Living Organis | 1971 | Chapman and Hall | **monograph** | low | curated_pure | default:no_signals |
| 2111 | Urban Dynamics: Extensions and Reflections | 1972 | San Francisco Press | **monograph** | low | curated_pure | default:no_signals |
| 2130 | Theory and World Politics | 1972 | Winthrop | **monograph** | low | curated_pure | default:no_signals |
| 2164 | Cybernetic Creativity | 1972 | R. Speller | **monograph** | low | title_corroborated | default:no_signals |
| 2165 | Cybernetic Aspects of Language | 1972 | Mouton | **monograph** | low | title_corroborated | default:no_signals |
| 2668 | Laws of Form | 1972 | Julian Press | **monograph** | low | curated_pure | default:no_signals |
| 2670 | Mathematical Structure of Finite Random Cyber | 1972 | Springer Vienna | **monograph** | medium | title_only | publisher:springer |
| 2057 | Ecclesial Cybernetics: A Study of Democracy i | 1973 | Macmillan | **monograph** | low | title_corroborated | default:no_signals |
| 2114 | Sexual Cybernetics | 1973 | Pinnacle Books | **monograph** | low | title_corroborated | default:no_signals |
| 2138 | Cybernetic and Sculpture Environnement | 1973 | Galerie Denise René | **monograph** | low | title_only | default:no_signals |
| 2241 | Cybernetic Engineering | 1973 | Butterworths | **monograph** | low | title_only | default:no_signals |
| 2433 | Birth & Death & Cybernation | 1973 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2291 | The Cybernetic Theory of Development Mathemat | 1974 | Kustannusosakeyhtio  | **monograph** | low | title_only | default:no_signals |
| 2467 | The Cyberiad; Fables for the Cybernetic Age | 1974 | Seabury Press | **monograph** | low | title_corroborated | default:no_signals |
| 2525 | The Cybernetic Revolution | 1974 | Barnes & Noble Books | **monograph** | low | title_corroborated | default:no_signals |
| 2544 | Communication and Organizational Control: Cyb | 1974 | Wiley | **monograph** | low | title_corroborated | default:no_signals |
| 2746 | Cybernetics a to Z | 1974 | Mir Publishers | **monograph** | low | title_corroborated | default:no_signals |
| 2054 | Engineering Cybernetics | 1975 | Prentice-Hall | **monograph** | low | title_corroborated | default:no_signals |
| 2106 | Cybernetic Approach to Stock Market Analysis, | 1975 | Exposition Press | **monograph** | low | title_corroborated | default:no_signals |
| 2139 | The Intelligent Universe: A Cybernetic Philos | 1975 | Putnam | **monograph** | low | title_corroborated | default:no_signals |
| 2614 | Conversation, Cognition and Learning: A Cyber | 1975 | Elsevier | **monograph** | low | title_only | default:no_signals |
| 2754 | The Cybernetics of Human Learning and Perform | 1975 | Taylor & Francis Gro | **monograph** | low | title_corroborated | default:no_signals |
| 2055 | Instructional Regulation and Control: Cyberne | 1976 | Educational Technolo | **monograph** | low | title_corroborated | default:no_signals |
| 2159 | Cybernetic Methods in Chemistry & Chemical En | 1976 | Mir Publishers | **monograph** | low | title_corroborated | default:no_signals |
| 2168 | Biological Machines: A Cybernetic Approach to | 1976 | Edward Arnold | **monograph** | low | title_corroborated | default:no_signals |
| 2188 | Democracy at Work: The Report of the Norwegia | 1976 | Springer US | **monograph** | medium | curated_pure | publisher:springer |
| 2388 | Generalized Harmonic Analysis and Tauberian T | 1976 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2389 | Mathematical Philosophy and Foundations: Pote | 1976 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2616 | Conversation Theory: Applications in Educatio | 1976 | Elsevier | **monograph** | low | curated_pure | default:no_signals |
| 2219 | Systems Thinking: Concepts and Notions | 1977 | Martinus Nijhoff | **monograph** | low | curated_pure | default:no_signals |
| 2235 | The Foundations of Cybernetics | 1977 | Gordon and Breach | **monograph** | low | title_corroborated | default:no_signals |
| 2608 | Computers and the Cybernetic Society | 1977 | Academic Press | **monograph** | low | title_corroborated | default:no_signals |
| 2735 | The Phenomenon of Science | 1977 | Columbia Univ Pr | **monograph** | low | curated_keyword | default:no_signals |
| 2137 | The Stable Society: Its Structure and Control | 1978 | Wadebridge Press | **monograph** | low | title_only | default:no_signals |
| 2169 | Applied Cybernetics: Its Relevance in Operati | 1978 | Gordon and Breach | **monograph** | low | title_corroborated | default:no_signals |
| 2180 | The Rise of Systems Theory: An Ideological An | 1978 | Wiley | **monograph** | low | curated_keyword | default:no_signals |
| 2619 | Cultures of the Future | 1978 | Mouton | **monograph** | low | curated_pure | default:no_signals |
| 2109 | Urban Dynamics | 1979 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 2131 | Communication and Control in Society | 1979 | CRC Press | **monograph** | low | curated_keyword | default:no_signals |
| 2514 | The Heart of Enterprise | 1979 | Wiley | **monograph** | low | curated_pure | default:no_signals |
| 2676 | Mind and Nature: A Necessary Unity | 1979 | Dutton | **monograph** | low | curated_pure | default:no_signals |
| 2690 | Philosophical Foundations of Cybernetics | 1979 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2112 | System Dynamics | 1980 | North-Holland Publis | **monograph** | low | curated_pure | default:no_signals |
| 2523 | The Cybernetic Imagination in Science Fiction | 1980 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2543 | Economic Cybernetics | 1980 | Abacus Press | **monograph** | low | title_corroborated | default:no_signals |
| 2595 | Autopoiesis and Cognition: The Realization of | 1980 | D. Reidel Publishing | **monograph** | low | curated_pure | default:no_signals |
| 2749 | John Von Neumann and Norbert Wiener: From Mat | 1980 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2153 | Cybernetics and Society: An Analysis of Socia | 1981 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2387 | The Hopf-Wiener Integral Equation: Prediction | 1981 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2546 | The Creation of Life: A Cybernetic Approach t | 1981 | Master Books | **monograph** | low | title_corroborated | default:no_signals |
| 2611 | Control and Ability: Towards a Biocybernetics | 1981 | John Benjamins Publi | **monograph** | low | title_corroborated | default:no_signals |
| 2666 | Mechanisms of Intelligence: Ashby's Writings  | 1981 | Intersystems Publica | **monograph** | low | title_corroborated | default:no_signals |
| 2051 | Systems Theory and Family Therapy: A Primer | 1982 | University Press of  | **monograph** | low | curated_pure | default:no_signals |
| 2602 | Biological Foundations of Linguistic Communic | 1982 | John Benjamins Publi | **monograph** | low | title_corroborated | default:no_signals |
| 2638 | Cybernetics Within Us | 1982 | Wilshire Book Compan | **monograph** | low | title_only | default:no_signals |
| 2171 | Management Principles and Practice: A Cyberne | 1983 | Gordon and Breach Sc | **monograph** | low | title_corroborated | default:no_signals |
| 2229 | Aesthetics of Change | 1983 | Guilford Publication | **monograph** | low | curated_keyword | default:no_signals |
| 2414 | The Tree of Knowledge: The Biological Roots o | 1983 | Shambhala | **monograph** | low | curated_pure | default:no_signals |
| 2534 | Cybernetics, Theory and Applications | 1983 | Hemisphere Pub | **monograph** | low | title_only | default:no_signals |
| 2548 | A Cybernetic Approach to Colour Perception | 1983 | Gordon and Breach Sc | **monograph** | low | title_corroborated | default:no_signals |
| 2716 | The Cybernetic Foundation Mathematics | 1983 | The City University  | **monograph** | low | title_only | default:no_signals |
| 2528 | The Science of History: A Cybernetic Approach | 1984 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2752 | Observing Systems | 1984 | Intersystems Publica | **monograph** | low | curated_keyword | default:no_signals |
| 2161 | Cybernetic Music | 1985 | Tab Books | **monograph** | low | title_corroborated | default:no_signals |
| 2357 | Cybernetics, Science, and Society; Ethics, Ae | 1985 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2513 | Diagnosing the System for Organizations | 1985 | Wiley | **monograph** | low | curated_keyword | default:no_signals |
| 2141 | Organizational Cybernetics and Business Polic | 1986 | Pennsylvania State U | **monograph** | low | title_corroborated | default:no_signals |
| 2236 | Cybernetic Medley | 1986 | Mir Publishers Mosco | **monograph** | low | title_corroborated | default:no_signals |
| 2308 | The Control Revolution: Technological and Eco | 1986 | Harvard University P | **monograph** | low | curated_pure | default:no_signals |
| 2516 | Pebbles to Computers: The Thread | 1986 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 2538 | Beyond Mechanization: Work and Technology in  | 1986 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2689 | Power, Autonomy, Utopia: New Approaches Towar | 1986 | Springer | **monograph** | medium | curated_keyword | publisher:springer |
| 2432 | Art in the Science Dominated World: Science,  | 1987 | Taylor & Francis | **monograph** | low | curated_keyword | default:no_signals |
| 2526 | Brains, Machines, and Mathematics | 1987 | Springer Verlag | **monograph** | medium | curated_keyword | publisher:springer |
| 2730 | The Media Lab: Inventing the Future at MIT | 1987 | Viking | **monograph** | low | curated_pure | default:no_signals |
| 2166 | Computers, Automation, and Cybernetics at the | 1989 | The Museum | **monograph** | low | title_corroborated | default:no_signals |
| 2359 | Ecological Communication | 1989 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 2522 | Freedom From Stress: Most People Deal With Sy | 1989 | Brandt Pub. | **monograph** | low | title_corroborated | default:no_signals |
| 2726 | The Human Use of Human Beings: Cybernetics an | 1989 | Free Association | **monograph** | low | title_corroborated | default:no_signals |
| 2194 | Biological Feedback | 1990 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 2394 | The Age of Intelligent Machines | 1990 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2701 | Self-Steering and Cognition in Complex System | 1990 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2162 | Cybernetics: A New Management Tool | 1991 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2183 | A Cyborg Manifesto | 1991 |  | **monograph** | low | curated_keyword | default:no_signals |
| 2462 | Radical Constructivism in Mathematics Educati | 1991 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2504 | Simians, Cyborgs and Women: The Reinvention o | 1991 | Free Association Boo | **monograph** | low | curated_keyword | default:no_signals |
| 2506 | Life Itself: A Comprehensive Inquiry Into the | 1991 | Columbia University  | **monograph** | low | curated_pure | default:no_signals |
| 2539 | How Colleges Work: The Cybernetics of Academi | 1991 | John Wiley & Sons | **monograph** | low | title_corroborated | default:no_signals |
| 2592 | A Sacred Unity: Further Steps to an Ecology o | 1991 | Cornelia & Michael B | **monograph** | low | curated_pure | default:no_signals |
| 2647 | Feedback Thought in Social Science and System | 1991 | University of Pennsy | **monograph** | low | curated_pure | default:no_signals |
| 2675 | New Perspectives on Cybernetics: Self-Organiz | 1991 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2704 | Sociocybernetics: A Perspective for Living in | 1992 | Social Systems Press | **monograph** | low | title_corroborated | default:no_signals |
| 2113 | Systemic Psychotherapy With Families, Couples | 1993 | Jason Aronson | **monograph** | low | curated_pure | default:no_signals |
| 2142 | Organisational Fitness: Corporate Effectivene | 1993 | Campus Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 2150 | Cybernetics in Water Resources Management | 1993 | Water Resources Publ | **monograph** | low | title_corroborated | default:no_signals |
| 2644 | Designing Freedom | 1993 | House of Anansi | **monograph** | low | curated_keyword | default:no_signals |
| 2125 | Cyberia: Life in the Trenches of Hyperspace | 1994 | Flamingo | **monograph** | low | curated_keyword | default:no_signals |
| 2167 | Biological Psychology: A Cybernetic Science | 1994 | Prentice Hall | **monograph** | low | title_corroborated | default:no_signals |
| 2482 | The Cybernetics of Prejudices in the Practice | 1994 | Karnac Books | **monograph** | low | title_only | default:no_signals |
| 2511 | Beyond Dispute: The Invention of Team Syntegr | 1994 | Wiley | **monograph** | low | curated_keyword | default:no_signals |
| 2517 | Invention: The Care and Feeding of Ideas | 1994 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2261 | A Recursive Vision: Ecological Understanding  | 1995 | University of Toront | **monograph** | low | curated_pure | default:no_signals |
| 2360 | Social Systems | 1995 | Stanford University  | **monograph** | low | curated_keyword | default:no_signals |
| 2488 | Radical Constructivism: A Way of Knowing and  | 1995 | Falmer Press | **monograph** | low | curated_keyword | default:no_signals |
| 2527 | Reasoning Into Reality: A System-Cybernetics  | 1995 | Wisdom Publications | **monograph** | low | title_corroborated | default:no_signals |
| 2688 | Platform for Change | 1995 | Wiley | **monograph** | low | curated_pure | default:no_signals |
| 2745 | Brain of the Firm | 1995 | Wiley | **monograph** | low | curated_pure | default:no_signals |
| 2172 | Systemic Therapy With Individuals | 1996 | Karnac Books | **monograph** | low | curated_pure | default:no_signals |
| 2497 | Cyberspace/Cyberbodies/Cyberpunk: Cultures of | 1996 | SAGE | **monograph** | low | curated_pure | default:no_signals |
| 2678 | Neural Networks as Cybernetic Systems | 1996 | G. Thieme Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 2406 | Without Miracles: Universal Selection Theory  | 1997 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2712 | Technobrat: Culture in a Cybernetic Classroom | 1997 | HarperCollins Publ.  | **monograph** | low | title_only | default:no_signals |
| 2136 | Volleyball Cybernetics | 1998 | "Yes, I can!" Public | **monograph** | low | title_only | default:no_signals |
| 2674 | Making Sense of Behavior: The Meaning of Cont | 1998 | Benchmark Publicatio | **monograph** | low | curated_pure | default:no_signals |
| 2257 | How Brains Make Up Their Minds | 1999 | Weidenfeld & Nicolso | **monograph** | low | curated_pure | default:no_signals |
| 2258 | Management Systems: A Viable Systems Approach | 1999 | Financial Times Mana | **monograph** | low | curated_pure | default:no_signals |
| 2377 | Perspectives on Behavioral Self-Regulation | 1999 | L. Erlbaum Asociates | **monograph** | low | curated_pure | default:no_signals |
| 2662 | How We Became Posthuman: Virtual Bodies in Cy | 1999 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 2108 | The Mechanization of the Mind: On the Origins | 2000 | Princeton University | **monograph** | low | curated_keyword | default:no_signals |
| 2320 | Gaia: A New Look at Life on Earth | 2000 | OUP Oxford | **monograph** | low | curated_pure | default:no_signals |
| 2366 | Art as a Social System | 2000 | Stanford University  | **monograph** | low | curated_keyword | default:no_signals |
| 2367 | The Reality of the Mass Media | 2000 | Stanford University  | **monograph** | low | curated_keyword | default:no_signals |
| 2695 | Quantum Cybernetics: Toward a Unification of  | 2000 | Springer | **monograph** | medium | title_only | publisher:springer |
| 2740 | The Things We Do: Using the Lessons of Bernar | 2000 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2053 | Living Systems: Theory and Application | 2001 | Nova Science Publish | **monograph** | low | curated_pure | default:no_signals |
| 2402 | On the Self-Regulation of Behavior | 2001 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 2496 | The Modern Invention of Information: Discours | 2001 | SIU Press | **monograph** | low | curated_pure | default:no_signals |
| 2533 | The Dream of Reality: Heinz Von Foerster’s Co | 2001 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2705 | Sociocybernetics: Complexity, Autopoiesis, an | 2001 | Bloomsbury Publishin | **monograph** | low | title_corroborated | default:no_signals |
| 2177 | Theories of Distinction: Redescribing the Des | 2002 | Stanford University  | **monograph** | low | curated_pure | default:no_signals |
| 2248 | Control Theory for Humans: Quantitative Appro | 2002 | Taylor & Francis | **monograph** | low | curated_pure | default:no_signals |
| 2413 | More Mind Readings: Methods and Models in the | 2002 | New View Publication | **monograph** | low | curated_pure | default:no_signals |
| 2463 | Radical Constructivism in Action: Building on | 2002 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2536 | The Cybernetic Theory of Decision: New Dimens | 2002 | Princeton University | **monograph** | low | title_corroborated | default:no_signals |
| 2540 | From Energy to Information: Representation in | 2002 | Stanford University  | **monograph** | low | curated_pure | default:no_signals |
| 2598 | Between Human and Machine: Feedback, Control, | 2002 | JHU Press | **monograph** | low | title_corroborated | default:no_signals |
| 2750 | Marine Control Systems: Guidance, Navigation  | 2002 | Marine Cybernetics | **monograph** | low | curated_pure | default:no_signals |
| 2756 | The PSYCHOCYBERNETIC MODEL OF ART THERAPY: (2 | 2002 | Charles C Thomas Pub | **monograph** | low | title_corroborated | default:no_signals |
| 2764 | The Cyberiad: Stories | 2002 | HMH | **monograph** | low | curated_keyword | default:no_signals |
| 2050 | Understanding Systems: Conversations on Epist | 2003 | Springer US | **monograph** | medium | curated_pure | publisher:springer |
| 2132 | Communication and Cyberspace: Social Interact | 2003 | Hampton Press | **monograph** | low | curated_keyword | default:no_signals |
| 2173 | Natural-Born Cyborgs: Minds, Technologies, an | 2003 | Oxford University Pr | **monograph** | low | metadata_search | default:no_signals |
| 2174 | Autopoietic Organization Theory: Drawing on N | 2003 | Abstrakt forlag | **monograph** | low | curated_pure | default:no_signals |
| 2218 | Telematic Embrace: Visionary Theories of Art, | 2003 | University of Califo | **monograph** | low | curated_keyword | default:no_signals |
| 2343 | Nature's Magic: Synergy in Evolution and the  | 2003 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 2405 | People as Living Things: The Psychology of Pe | 2003 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2428 | Self-Organization in Biological Systems | 2003 | Princeton University | **monograph** | low | curated_pure | default:no_signals |
| 2481 | The Evolutionary Trajectory: The Growth of In | 2003 | CRC Press | **monograph** | low | curated_keyword | default:no_signals |
| 2613 | Control and Modeling of Complex Systems: Cybe | 2003 | Birkhäuser | **monograph** | low | title_corroborated | default:no_signals |
| 2702 | Rethinking Homeostasis: Allostatic Regulation | 2003 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2766 | Anticipatory Behavior in ALS: Foundations, Th | 2003 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2767 | Narrative Gravity: Conversation, Cognition, C | 2003 | Routledge | **monograph** | low | metadata_search | default:no_signals |
| 2122 | March of the Machines: The Breakthrough in Ar | 2004 | University of Illino | **monograph** | low | curated_keyword | default:no_signals |
| 2175 | Law as a Social System | 2004 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 2430 | Creativity as an Exact Science | 2004 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 2501 | Developing Second Order Cybernetics | 2004 | Emerald Group Publis | **monograph** | low | title_corroborated | default:no_signals |
| 2562 | From Being to Doing: The Origins of the Biolo | 2004 | Carl-Auer Verlag | **monograph** | low | curated_pure | default:no_signals |
| 2673 | Machines Who Think: A Personal Inquiry Into t | 2004 | Taylor & Francis | **monograph** | low | curated_pure | default:no_signals |
| 2743 | Tribute to Stafford Beer | 2004 | Emerald Group Publis | **monograph** | low | curated_keyword | default:no_signals |
| 2117 | Understanding Me: Lectures and Interviews | 2005 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2363 | Risk: A Sociological Theory | 2005 | Aldine Transaction | **monograph** | low | curated_pure | default:no_signals |
| 2494 | Cultures of Control | 2005 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2499 | Heinz von Foerster - in memoriam | 2005 | Emerald Publishing | **monograph** | low | curated_pure | default:no_signals |
| 2597 | Behavior: The Control of Perception | 2005 | Benchmark Publicatio | **monograph** | low | curated_pure | default:no_signals |
| 2659 | Holistic Darwinism: Synergy, Cybernetics, and | 2005 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 2681 | On Purposeful Systems: An Interdisciplinary A | 2005 | Aldine Transaction | **monograph** | low | curated_pure | default:no_signals |
| 2738 | The Semantic Turn: A New Foundation for Desig | 2005 | Taylor & Francis | **monograph** | low | curated_pure | default:no_signals |
| 2763 | World Weavers: Globalization, Science Fiction | 2005 | Hong Kong University | **monograph** | low | title_corroborated | default:no_signals |
| 2105 | Digital Shock: Confronting the New Reality | 2006 |  | **monograph** | low | curated_keyword | default:no_signals |
| 2176 | Luhmann Explained: From Souls to Systems | 2006 | Open Court Publishin | **monograph** | low | curated_keyword | default:no_signals |
| 2324 | Self-Organization and Emergence in Life Scien | 2006 | Springer | **monograph** | medium | metadata_search | publisher:springer |
| 2484 | Festschrift for Felix Geyer | 2006 | Emerald Publishing | **monograph** | low | curated_pure | default:no_signals |
| 2551 | Collective Beings | 2006 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer |
| 2630 | Cybernetics and Public Administration | 2006 | Emerald Publishing | **monograph** | low | title_only | default:no_signals |
| 2652 | From Counterculture to Cyberculture: Stewart  | 2006 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 2184 | Composing a Life | 2007 | Grove Press | **monograph** | low | curated_pure | default:no_signals |
| 2254 | Casting Nets and Testing Specimens: Two Grand | 2007 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2401 | Systems Biology: Philosophical Foundations | 2007 | Elsevier | **monograph** | low | curated_pure | default:no_signals |
| 2418 | Cybernetical Physics: From Control of Chaos t | 2007 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2449 | Imaginary Futures: From Thinking Machines to  | 2007 | Pluto Press | **monograph** | low | curated_pure | default:no_signals |
| 2461 | Key Works in Radical Constructivism | 2007 | Sense Publishers | **monograph** | low | curated_pure | default:no_signals |
| 2485 | Beginning of a New Epistemology - In Memoriam | 2007 | Emerald Publishing | **monograph** | low | curated_pure | default:no_signals |
| 2542 | Biological Cybernetics Research Trends | 2007 | Nova Publishers | **monograph** | low | title_corroborated | default:no_signals |
| 2561 | Neocybernetics in Biological Systems | 2007 | Helsinki University  | **monograph** | low | title_only | default:no_signals |
| 2588 | Anticipatory Behavior in ALS: From Brains to  | 2007 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2591 | Architectural Principles in the Age of Cybern | 2007 | Routledge | **monograph** | low | title_only | default:no_signals |
| 2626 | Cybernetics and Design | 2007 | Emerald Group Publis | **monograph** | low | title_only | default:no_signals |
| 2179 | Communication: The Social Matrix of Psychiatr | 2008 | Transaction Publishe | **monograph** | low | curated_pure | default:no_signals |
| 2189 | Living Control Systems III: The Fact of Contr | 2008 |  | **monograph** | low | curated_pure | default:no_signals |
| 2260 | The Mechanical Mind in History | 2008 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2316 | Systems Research for Behavioral Science: A So | 2008 | Transaction Publishe | **monograph** | low | curated_keyword | default:no_signals |
| 2407 | Management and Leadership: Insight for Effect | 2008 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2478 | Reviving the Living: Meaning Making in Living | 2008 | Elsevier Science | **monograph** | low | curated_pure | default:no_signals |
| 2503 | Posthuman Metamorphosis: Narrative and System | 2008 | Fordham University P | **monograph** | low | curated_keyword | default:no_signals |
| 2581 | A Legacy for Living Systems: Gregory Bateson  | 2008 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2607 | Constructing Soviet Cultural Policy: Cybernet | 2008 | Tema Q (Culture Stud | **monograph** | low | title_only | default:no_signals |
| 2640 | Cybersemiotics: Why Information Is Not Enough | 2008 | University of Toront | **monograph** | low | curated_keyword | default:no_signals |
| 2680 | On Communicating: Otherness, Meaning, and Inf | 2008 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2714 | The Challenge of Anticipation: A Unifying Fra | 2008 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer |
| 2715 | The Allure of Machinic Life: Cybernetics, Art | 2008 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2220 | Digital Culture | 2009 | Reaktion Books | **monograph** | low | curated_pure | default:no_signals |
| 2231 | The Scientific Way of Warfare: Order and Chao | 2009 | Columbia University  | **monograph** | low | curated_keyword | default:no_signals |
| 2358 | Autopoiesis in Organization Theory and Practi | 2009 | Emerald Publishing L | **monograph** | low | curated_pure | default:no_signals |
| 2396 | Cyburbia : The Dangerous Idea That's Changing | 2009 | Little Brown | **monograph** | low | curated_pure | default:no_signals |
| 2515 | Think Before You Think: Social Complexity and | 2009 | Wavestone Press | **monograph** | low | curated_keyword | default:no_signals |
| 2530 | Sociology and Complexity Science: A New Field | 2009 | Springer | **monograph** | medium | metadata_search | publisher:springer |
| 2584 | A Missing Link in Cybernetics | 2009 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2646 | Emotional Intelligence: A Cybernetic Approach | 2009 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2722 | The Digital Cast of Being: Metaphysics, Mathe | 2009 | Ontos-Verlag | **monograph** | low | title_only | default:no_signals |
| 2052 | Controlling Uncertainty: Decision Making and  | 2010 | Wiley | **monograph** | low | curated_pure | default:no_signals |
| 2095 | Cyborgs in Latin America | 2010 | Palgrave Macmillan U | **monograph** | low | curated_pure | default:no_signals |
| 2214 | Organizations: Social Systems Conducting Expe | 2010 | Springer Berlin Heid | **monograph** | medium | curated_keyword | publisher:springer |
| 2319 | Gaia in Turmoil: Climate Change, Biodepletion | 2010 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2323 | Cyberfiction: After the Future | 2010 | Palgrave Macmillan | **monograph** | low | curated_keyword | default:no_signals |
| 2385 | Project: Soul Catcher: Secrets of Cyber and C | 2010 | CreateSpace Independ | **monograph** | low | title_corroborated | default:no_signals |
| 2412 | Dialogue Concerning the Two Chief Approaches  | 2010 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2578 | A Foray Into the Worlds of Animals and Humans | 2010 | Univ Of Minnesota Pr | **monograph** | low | curated_pure | default:no_signals |
| 2580 | Ahead of Change: How Crowd Psychology and Cyb | 2010 | Campus Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 2721 | The Discovery of the Artificial: Behavior, Mi | 2010 | Springer Netherlands | **monograph** | medium | title_only | publisher:springer |
| 2124 | This Is Not a Program | 2011 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2253 | The Dilemma of Enquiry and Learning | 2011 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2295 | The Creation of Reality: A Constructivist Epi | 2011 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2301 | Cybernetic Revolutionaries: Technology and Po | 2011 | The MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2314 | Computation in Cells and Tissues: Perspective | 2011 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2435 | Relative Information: Theories and Applicatio | 2011 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2576 | A Cybernetic View of Biological Growth: The M | 2011 | Cambridge University | **monograph** | low | title_corroborated | default:no_signals |
| 2610 | Context and Complexity: Cultivating Contextua | 2011 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2683 | Organizational Systems: Managing Complexity W | 2011 | Springer Berlin Heid | **monograph** | medium | curated_keyword | publisher:springer |
| 2687 | Perspectives on Information | 2011 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2693 | Process Control A Practical Approach | 2011 | Wiley | **monograph** | low | curated_pure | default:no_signals |
| 2713 | The Cybernetic Brain: Sketches of Another Fut | 2011 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 2094 | A More Developed Sign: Interpreting the Work  | 2012 | Tartu University Pre | **monograph** | low | curated_pure | default:no_signals |
| 2197 | Autopoiesis and Configuration Theory: New App | 2012 | Springer Netherlands | **monograph** | medium | curated_pure | publisher:springer |
| 2250 | Control in the Classroom: An Adventure in Lea | 2012 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2255 | Ways of Learning and Knowing: The Epistemolog | 2012 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2382 | A Choice of Futures | 2012 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer |
| 2383 | Futures We Are In | 2012 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer |
| 2429 | Design and Diagnosis for Sustainable Organiza | 2012 | Springer Science & B | **monograph** | medium | curated_keyword | publisher:springer |
| 2502 | Information Theory and Evolution | 2012 | World Scientific | **monograph** | low | metadata_search | default:no_signals |
| 2524 | Positive Feedback in Natural Systems | 2012 | Springer Berlin Heid | **monograph** | medium | curated_keyword | publisher:springer |
| 2552 | The Application of Cybernetic Analysis to the | 2012 | Springer | **monograph** | medium | title_only | publisher:springer |
| 2571 | The Origin of Humanness in the Biology of Lov | 2012 | Andrews UK Limited | **monograph** | low | curated_pure | default:no_signals |
| 2586 | Anticipatory Systems: Philosophical, Mathemat | 2012 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2623 | Cybernetic Revelation: Deconstructing Artific | 2012 | Post Egoism Media | **monograph** | low | title_corroborated | default:no_signals |
| 2665 | Information and Reflection: On Some Problems  | 2012 | Springer Science & B | **monograph** | medium | title_corroborated | publisher:springer |
| 2682 | Organization Structure: Cybernetic Systems Fo | 2012 | Springer Science & B | **monograph** | medium | title_corroborated | publisher:springer |
| 2061 | Probability Theory, Mathematical Statistics,  | 2013 | Springer Science & B | **monograph** | medium | title_only | publisher:springer |
| 2252 | The Death of Jeffrey Stapleton: Exploring the | 2013 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2280 | Self-Producing Systems: Implications and Appl | 2013 | Springer US | **monograph** | medium | curated_pure | publisher:springer |
| 2464 | Summa Technologiae | 2013 | U of Minnesota Press | **monograph** | low | curated_pure | default:no_signals |
| 2479 | Purposive Explanation in Psychology | 2013 | Harvard University P | **monograph** | low | curated_pure | default:no_signals |
| 2537 | The Cybernetic Society: Pergamon Unified Engi | 2013 | Elsevier | **monograph** | low | title_corroborated | default:no_signals |
| 2570 | The Certainty of Uncertainty: Dialogues Intro | 2013 | Andrews UK Limited | **monograph** | low | curated_keyword | default:no_signals |
| 2617 | Culture Contact in Evenki Land: A Cybernetic  | 2013 | Global Oriental | **monograph** | low | title_corroborated | default:no_signals |
| 2618 | Cybernetic Approach to Project Management | 2013 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2669 | Knowledge and Systems Science: Enabling Syste | 2013 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 2686 | Polish Cybernetic Poetry | 2013 |  | **monograph** | low | title_only | default:no_signals |
| 2694 | Processes and Boundaries of the Mind: Extendi | 2013 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer |
| 2742 | Traditions of Systems Theory: Major Figures a | 2013 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2769 | Systems Methodology for the Management Scienc | 2013 | Springer US | **monograph** | medium | metadata_search | publisher:springer |
| 2187 | Ontology of Complexity: A Reading of Gregory  | 2014 | CreateSpace Independ | **monograph** | low | curated_keyword | default:no_signals |
| 2283 | From Cells to Societies: Models of Complex Co | 2014 | Springer Berlin Heid | **monograph** | medium | curated_pure | publisher:springer |
| 2395 | Virtually Human: The Promise—and the Peril—of | 2014 | St. Martin's Press | **monograph** | low | curated_pure | default:no_signals |
| 2445 | Indexing It All: The Subject in the Age of Do | 2014 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2457 | The Unleashed Scandal: The End of Control in  | 2014 | Andrews UK Limited | **monograph** | low | curated_pure | default:no_signals |
| 2480 | Biomolecular Feedback Systems | 2014 | Princeton University | **monograph** | low | curated_pure | default:no_signals |
| 2550 | The Magic Ring: Systems Thinking Approach to  | 2014 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2566 | Rhetoric and Ethics in the Cybernetic Age: Th | 2014 | Routledge | **monograph** | low | title_only | default:no_signals |
| 2629 | Cybernetics and the Philosophy of Mind | 2014 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2664 | Innovative Approaches Towards Low Carbon Econ | 2014 | Springer Berlin Heid | **monograph** | medium | title_only | publisher:springer |
| 2672 | Neocybernetics and Narrative | 2014 | U of Minnesota Press | **monograph** | low | title_corroborated | default:no_signals |
| 2700 | Reflexion and Control: Mathematical Models | 2014 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 2753 | The Beginning of Heaven and Earth Has No Name | 2014 | Fordham University P | **monograph** | low | title_corroborated | default:no_signals |
| 2196 | Karl W. Deutsch: Pioneer in the Theory of Int | 2015 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer |
| 2263 | Earth, Life, and System: Evolution and Ecolog | 2015 | Fordham University P | **monograph** | low | curated_pure | default:no_signals |
| 2267 | Cyber-Proletariat: Global Labour in the Digit | 2015 | Pluto Press | **monograph** | low | curated_pure | default:no_signals |
| 2287 | Jakob Von Uexküll: The Discovery of the Umwel | 2015 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2310 | Anticipation: Learning From the Past: The Rus | 2015 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2560 | @Heaven: The Online Death of a Cybernetic Fut | 2015 | OR Books | **monograph** | low | title_only | default:no_signals |
| 2569 | The Internet Revolution: From Dot-Com Capital | 2015 | Institute of Network | **monograph** | low | title_corroborated | default:no_signals |
| 2579 | Alleys of Your Mind: Augmented Intelligence a | 2015 | Meson Press | **monograph** | low | curated_keyword | default:no_signals |
| 2604 | Cognitive Systems | 2015 |  | **monograph** | low | curated_keyword | default:no_signals |
| 2609 | Control: Digitality as Cultural Logic | 2015 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2612 | Controlling People: The Paradoxical Nature of | 2015 | Australian Academic  | **monograph** | low | curated_pure | default:no_signals |
| 2632 | Cybernetics: From Past to Future | 2015 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2643 | Systems | 2015 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2651 | General System Theory: Foundations, Developme | 2015 | George Braziller Inc | **monograph** | low | curated_pure | default:no_signals |
| 2720 | The Cybernetics Moment: Or Why We Call Our Ag | 2015 | JHU Press | **monograph** | low | title_corroborated | default:no_signals |
| 2099 | Machines of Loving Grace: The Quest for Commo | 2016 | HarperCollins | **monograph** | low | curated_pure | default:no_signals |
| 2227 | Machine Art in the Twentieth Century | 2016 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2228 | New Tendencies: Art at the Threshold of the I | 2016 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2284 | Small Arcs of Larger Circles: Framing Through | 2016 | Triarchy Press | **monograph** | low | curated_pure | default:no_signals |
| 2286 | Cultural Implications of Biosemiotics | 2016 | Springer Netherlands | **monograph** | medium | curated_pure | publisher:springer |
| 2379 | The Power of Systems: How Policy Sciences Ope | 2016 | Cornell University P | **monograph** | low | curated_keyword | default:no_signals |
| 2403 | Perceptual Control Theory: An Overview of the | 2016 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2411 | Hold That Thought: Two Steps to Effective Cou | 2016 | New View Publication | **monograph** | low | curated_pure | default:no_signals |
| 2437 | Anticipation and Medicine | 2016 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2627 | Cybernetics and Development: International Se | 2016 | Elsevier | **monograph** | low | title_corroborated | default:no_signals |
| 2636 | Cybernetics: The Macy Conferences 1946-1953 : | 2016 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 2679 | On the Existence of Digital Objects | 2016 | University of Minnes | **monograph** | low | curated_pure | default:no_signals |
| 2697 | Rebel Genius: Warren S. McCulloch's Transdisc | 2016 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2710 | Strategy for Managing Complex Systems: A Cont | 2016 | Campus Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 2733 | The Question Concerning Technology in China:  | 2016 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2741 | Architecture and Adaptation: From Cybernetics | 2016 | Routledge, Taylor &  | **monograph** | low | title_only | default:no_signals |
| 2089 | Posthumanism and the Graphic Novel in Latin A | 2017 | UCL Press | **monograph** | low | curated_pure | default:no_signals |
| 2206 | Application of New Cybernetics in Physics | 2017 | Elsevier Science | **monograph** | low | title_corroborated | default:no_signals |
| 2294 | Border Security: Shores of Politics, Horizons | 2017 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2374 | Trust and Power | 2017 | Polity | **monograph** | low | curated_pure | default:no_signals |
| 2441 | A Complexity Approach to Sustainability: Theo | 2017 | World Scientific | **monograph** | low | curated_pure | default:no_signals |
| 2442 | Unthought: The Power of the Cognitive Noncons | 2017 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 2446 | How the Mind Comes Into Being | 2017 | Oxford University Pr | **monograph** | low | metadata_search | default:no_signals |
| 2453 | Intangible Life: Functorial Connections in Re | 2017 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2492 | Confronting the Machine: An Enquiry Into the  | 2017 | De Gruyter | **monograph** | low | curated_pure | default:no_signals |
| 2564 | New Horizons for Second-Order Cybernetics | 2017 | World Scientific | **monograph** | low | title_corroborated | default:no_signals |
| 2601 | Cinema, Trance and Cybernetics | 2017 | Amsterdam University | **monograph** | low | title_corroborated | default:no_signals |
| 2633 | Cybernetics: State of the Art | 2017 | Universitätsverlag d | **monograph** | low | title_corroborated | default:no_signals |
| 2634 | Cybernetics, Warfare and Discourse: The Cyber | 2017 | Springer Internation | **monograph** | medium | title_only | publisher:springer |
| 2723 | The Embodied Mind, Revised Edition: Cognitive | 2017 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2729 | The Nature of the Machine and the Collapse of | 2017 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer |
| 2765 | Applied Systems Theory | 2017 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer |
| 2771 | A Cybernetic Study of Speaking and Singing | 2017 | Cambridge Scholars P | **monograph** | low | title_only | default:no_signals |
| 2107 | Complexity Sciences: Theoretical and Empirica | 2018 | Cambridge Scholars P | **monograph** | low | curated_keyword | default:no_signals |
| 2262 | An Epistemology of Noise | 2018 | Bloomsbury Publishin | **monograph** | low | curated_pure | default:no_signals |
| 2318 | Gods and Robots: Myths, Machines, and Ancient | 2018 | Princeton University | **monograph** | low | curated_pure | default:no_signals |
| 2321 | Film in the Anthropocene: Philosophy, Ecology | 2018 | Palgrave Macmillan | **monograph** | low | title_corroborated | default:no_signals |
| 2325 | French Philosophy of Technology: Classical Re | 2018 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer |
| 2364 | Organization and Decision | 2018 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 2376 | Artificial Intelligence: Its Philosophy and N | 2018 | Routledge, Taylor &  | **monograph** | low | curated_pure | default:no_signals |
| 2378 | The Dream Machine | 2018 | Stripe Press | **monograph** | low | curated_pure | default:no_signals |
| 2381 | Energy, Information, Feedback, Adaptation, an | 2018 | Springer | **monograph** | medium | curated_keyword | publisher:springer |
| 2443 | Socially Extended Epistemology | 2018 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 2450 | Worldmaking as Techné: Participatory Art, Mus | 2018 | Riverside Architectu | **monograph** | low | curated_pure | default:no_signals |
| 2451 | Neural Network Modeling: Statistical Mechanic | 2018 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2455 | What Does It Mean to Be Human? Life, Death, P | 2018 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2489 | Routledge Library Editions: Artificial Intell | 2018 | Taylor & Francis Gro | **monograph** | low | metadata_search | default:no_signals |
| 2521 | Between an Animal and a Machine: Stanislaw Le | 2018 | Peter Lang | **monograph** | low | curated_keyword | default:no_signals |
| 2549 | From Collective Beings to Quasi-Systems | 2018 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2558 | Cybernetics and Systems: Social and Business  | 2018 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2559 | Cybernetics and Applied Systems | 2018 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 2567 | The Opening of the Cybernetic Frontier: Citie | 2018 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2574 | The Soft Machine: Cybernetic Fiction | 2018 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2649 | Flatline Constructs: Gothic Materialism and C | 2018 | Exmilitary | **monograph** | low | title_corroborated | default:no_signals |
| 2744 | Cybernetic Modeling for Bioreaction Engineeri | 2018 | Cambridge University | **monograph** | low | title_corroborated | default:no_signals |
| 2762 | What Is Information? | 2018 | University of Minnes | **monograph** | low | curated_pure | default:no_signals |
| 2067 | The Beauty of Detours: A Batesonian Philosoph | 2019 | SUNY Press | **monograph** | low | curated_pure | default:no_signals |
| 2069 | No More Feedback: Cultivate Consciousness at  | 2019 | InterOctave | **monograph** | low | curated_pure | default:no_signals |
| 2181 | Philosophical Posthumanism | 2019 | Bloomsbury Academic | **monograph** | low | curated_pure | default:no_signals |
| 2221 | The Meaning of Information | 2019 | Walter de Gruyter Gm | **monograph** | low | curated_pure | default:no_signals |
| 2299 | Thinking Race: Social Myths and Biological Re | 2019 | Rowman & Littlefield | **monograph** | low | curated_pure | default:no_signals |
| 2334 | Management Control Theory | 2019 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2345 | The Creative Therapist in Practice | 2019 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2347 | The Self-organizing Polity: An Epistemologica | 2019 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2427 | The Culture of Feedback: Ecological Thinking  | 2019 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 2447 | Documentarity: Evidence, Ontology, and Inscri | 2019 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2454 | Jim Dator: A Noticer in Time: Selected Work,  | 2019 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer |
| 2493 | Systems Theories for Psychotherapists: From T | 2019 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2498 | Communication as Gesture: Media(tion), Meanin | 2019 | Emerald Group Publis | **monograph** | low | curated_keyword | default:no_signals |
| 2500 | Rethinking Higher Education for the 21st Cent | 2019 | Emerald Publishing | **monograph** | low | curated_keyword | default:no_signals |
| 2557 | Design Cybernetics: Navigating the New | 2019 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer |
| 2575 | A Cybernetic Approach to the Assessment of Ch | 2019 | Taylor & Francis Gro | **monograph** | low | title_corroborated | default:no_signals |
| 2590 | Art, Cybernetics and Pedagogy in Post-War Bri | 2019 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2622 | Cybernetic frameworks for a shared world | 2019 | Springer | **monograph** | medium | title_corroborated | publisher:springer |
| 2625 | Cybernetics or Control and Communication in t | 2019 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2699 | Recursivity and Contingency | 2019 | Bloomsbury Academic | **monograph** | low | curated_keyword | default:no_signals |
| 2732 | Thermodynamics and Regulation of Biological P | 2019 | Walter de Gruyter Gm | **monograph** | low | curated_keyword | default:no_signals |
| 2758 | What Is Health? Allostasis and the Evolution  | 2019 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2070 | The Systemic Approach in Sociology and Niklas | 2020 | Emerald Publishing L | **monograph** | low | curated_pure | default:no_signals |
| 2071 | The American Robot: A Cultural History | 2020 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 2072 | Understanding the Knowledge Society: A New Pa | 2020 | Edward Elgar Publish | **monograph** | low | curated_pure | default:no_signals |
| 2091 | Machine Sensation: Anthropomorphism and 'Natu | 2020 | Open Humanities Pres | **monograph** | low | curated_keyword | default:no_signals |
| 2217 | Utopics: The Unification of Human Science | 2020 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer |
| 2278 | Think Tank Aesthetics: Midcentury Modernism,  | 2020 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2312 | For the Love of Cybernetics: Personal Narrati | 2020 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2346 | Jakob Von Uexküll and Philosophy: Life, Envir | 2020 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2375 | The Hidden Power of Systems Thinking: Governa | 2020 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2380 | Data Loam: Sometimes Hard, Usually Soft. The  | 2020 | Walter de Gruyter Gm | **monograph** | low | curated_pure | default:no_signals |
| 2431 | Resilience in the Anthropocene: Governance an | 2020 | Taylor & Francis Gro | **monograph** | low | curated_pure | default:no_signals |
| 2487 | Systems Thinking for a Turbulent World: A Sea | 2020 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2495 | Sociocybernetics and Political Theory in a Co | 2020 | BRILL | **monograph** | low | title_corroborated | default:no_signals |
| 2518 | Gregory Bateson on Relational Communication:  | 2020 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer |
| 2556 | Cybernetic Psychology and Mental Health: A Ci | 2020 | Routledge, Taylor &  | **monograph** | low | title_corroborated | default:no_signals |
| 2573 | Cybernetic-Existentialism: Freedom, Systems,  | 2020 | Taylor & Francis Gro | **monograph** | low | title_corroborated | default:no_signals |
| 2582 | Anarchist Cybernetics: Control and Communicat | 2020 | Policy Press | **monograph** | low | title_corroborated | default:no_signals |
| 2594 | Automated Media | 2020 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2642 | Discourses in Action: What Language Enables U | 2020 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2650 | Gaian Systems: Lynn Margulis, Neocybernetics, | 2020 | University of Minnes | **monograph** | low | title_corroborated | default:no_signals |
| 2717 | The Cybernetic Hypothesis | 2020 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 2046 | Embodiment of the Everyday Cyborg: Technologi | 2021 | Manchester Universit | **monograph** | low | curated_keyword | default:no_signals |
| 2073 | Sensing and Making Sense: Photosensitivity an | 2021 | Transcript | **monograph** | low | curated_keyword | default:no_signals |
| 2226 | Artificial Intelligence, Interaction, Perform | 2021 | Independently Publis | **monograph** | low | curated_pure | default:no_signals |
| 2259 | A Configuration Approach to Mindset Agency Th | 2021 | Cambridge University | **monograph** | low | curated_keyword | default:no_signals |
| 2330 | Agricultural Cybernetics | 2021 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer |
| 2341 | When Brains Meet Buildings | 2021 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 2355 | Cybernetics Without Mathematics | 2021 | Hassell Street Press | **monograph** | low | title_only | default:no_signals |
| 2386 | Adolescent Risk Behavior and Self-Regulation: | 2021 | Springer Nature | **monograph** | medium | title_only | publisher:springer |
| 2400 | Life Out of Balance: Homeostasis and Adaptati | 2021 | University Alabama P | **monograph** | low | curated_keyword | default:no_signals |
| 2466 | Dialogues | 2021 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2486 | Narratives of Scale in the Anthropocene: Imag | 2021 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2605 | Concerning Stephen Willats and the Social Fun | 2021 | Bloomsbury Publishin | **monograph** | low | title_corroborated | default:no_signals |
| 2631 | Cybernetics for the Social Sciences | 2021 | BRILL | **monograph** | low | title_corroborated | default:no_signals |
| 2639 | Deconstructing Health Inequity: A Perceptual  | 2021 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer |
| 2660 | Human 4.0: From Biology to Cybernetic | 2021 | BoD – Books on Deman | **monograph** | low | title_only | default:no_signals |
| 2698 | Recent Advances in Soft Computing and Cyberne | 2021 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer |
| 2719 | The Digitally Disposed: Racial Capitalism and | 2021 | University of Minnes | **monograph** | low | curated_keyword | default:no_signals |
| 2736 | Thinking by Machine: A Study of Cybernetics / | 2021 | Creative Media Partn | **monograph** | low | title_only | default:no_signals |
| 2737 | The Study of Living Control Systems: A Guide  | 2021 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 2090 | The Dark Posthuman: Dehumanization, Technolog | 2022 | punctum books | **monograph** | low | curated_keyword | default:no_signals |
| 2198 | Twins and Recursion in Digital, Literary and  | 2022 | Bloomsbury Academic | **monograph** | low | curated_keyword | default:no_signals |
| 2199 | Nervous Systems: Art, Systems, and Politics S | 2022 | Duke University Pres | **monograph** | low | curated_pure | default:no_signals |
| 2200 | Last Futures: Nature, Technology and the End  | 2022 | Verso Books | **monograph** | low | curated_pure | default:no_signals |
| 2204 | Architecture in Digital Culture: Machines, Ne | 2022 | Routledge/Taylor & F | **monograph** | low | curated_pure | default:no_signals |
| 2205 | Brainmedia: One Hundred Years of Performing L | 2022 | Bloomsbury Academic | **monograph** | low | curated_pure | default:no_signals |
| 2224 | Climatic Media: Transpacific Experiments in A | 2022 | Duke University Pres | **monograph** | low | curated_keyword | default:no_signals |
| 2277 | Designing Intelligent Construction Projects | 2022 | John Wiley & Sons | **monograph** | low | curated_keyword | default:no_signals |
| 2304 | Order in Chaos - Cybernetics of Brand Managem | 2022 | Springer Berlin Heid | **monograph** | medium | title_corroborated | publisher:springer |
| 2305 | The Informational Logic of Human Rights: Netw | 2022 | Edinburgh University | **monograph** | low | title_only | default:no_signals |
| 2311 | Artificial Intelligence in Accounting | 2022 | Routledge | **monograph** | low | metadata_search | default:no_signals |
| 2313 | Digital Fever: Taming the Big Business of Dis | 2022 | Palgrave Macmillan | **monograph** | low | curated_keyword | default:no_signals |
| 2322 | Complex System Governance: Theory and Practic | 2022 | Springer Internation | **monograph** | medium | metadata_search | publisher:springer |
| 2351 | Northern Sparks: Innovation, Technology Polic | 2022 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 2368 | The Making of Meaning: From the Individual to | 2022 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 2423 | Hormones and Reality: Epigenetic Regulation o | 2022 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer |
| 2424 | Semiotic Agency: Science Beyond Mechanism | 2022 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer |
| 2425 | The Neurology of Business: Implementing the V | 2022 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer |
| 2436 | Epigenetics and Anticipation | 2022 | Springer Nature | **monograph** | medium | curated_pure | publisher:springer |
| 2452 | Beyond Identities: Human Becomings in Weirdin | 2022 | Springer | **monograph** | medium | curated_pure | publisher:springer |
| 2490 | Sustainable Self-Governance in Businesses and | 2022 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 2520 | Cyber-Physical Systems: Theory, Methodology,  | 2022 | John Wiley & Sons | **monograph** | low | metadata_search | default:no_signals |
| 2555 | Cybernetic Architectures: Informational Think | 2022 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2603 | Complex Systems: Spanning Control and Computa | 2022 | Springer Internation | **monograph** | medium | title_only | publisher:springer |
| 2624 | Cybernetics 2.0: A General Theory of Adaptivi | 2022 | Springer | **monograph** | medium | title_only | publisher:springer |
| 2641 | Designing and Managing Complex Systems | 2022 | Elsevier Science | **monograph** | low | curated_pure | default:no_signals |
| 2648 | Ethical and Aesthetic Explorations of Systemi | 2022 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2708 | World Organization of Systems and Cybernetics | 2022 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer |
| 2728 | The New Technological Condition: Architecture | 2022 | Birkhäuser | **monograph** | low | title_corroborated | default:no_signals |
| 2077 | Interactive Design: Towards a Responsive Envi | 2023 | Walter de Gruyter Gm | **monograph** | low | curated_keyword | default:no_signals |
| 2078 | Experimenting the Human: Art, Music, and the  | 2023 | University of Chicag | **monograph** | low | curated_keyword | default:no_signals |
| 2082 | Algorithms: Technology, Culture, Politics | 2023 | Routledge, Taylor &  | **monograph** | low | curated_pure | default:no_signals |
| 2182 | Laws of Form: A Fiftieth Anniversary | 2023 | World Scientific | **monograph** | low | curated_pure | default:no_signals |
| 2202 | Organism-Oriented Ontology | 2023 | Edinburgh University | **monograph** | low | curated_pure | default:no_signals |
| 2223 | Art and Knowledge After 1900: Interactions Be | 2023 | Manchester Universit | **monograph** | low | curated_keyword | default:no_signals |
| 2225 | With and Against: The Situationist Internatio | 2023 | Verso Books | **monograph** | low | curated_keyword | default:no_signals |
| 2244 | Health as a Social System: Luhmann's Theory A | 2023 | transcript Verlag | **monograph** | low | curated_pure | default:no_signals |
| 2293 | Unstable Nature: Order, Entropy, Becoming | 2023 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 2339 | Frictions: Inquiries Into Cybernetic Thinking | 2023 | meson Press eG | **monograph** | low | title_corroborated | default:no_signals |
| 2349 | Art + DIY Electronics | 2023 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2350 | Evolution "On Purpose": Teleonomy in Living S | 2023 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2352 | Balkan Cyberia: Cold War Computing, Bulgarian | 2023 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2599 | Code: From Information Theory to French Theor | 2023 | Duke University Pres | **monograph** | low | curated_keyword | default:no_signals |
| 2620 | Cybernetical Intelligence: Engineering Cybern | 2023 | John Wiley & Sons | **monograph** | low | title_corroborated | default:no_signals |
| 2621 | Cybernetic Aesthetics: Modernist Networks of  | 2023 | Cambridge University | **monograph** | low | title_corroborated | default:no_signals |
| 2770 | The Experience Machine: How Our Minds Predict | 2023 | Pantheon | **monograph** | low | curated_pure | default:no_signals |
| 2080 | Organization Studies and Posthumanism: Toward | 2024 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2081 | Cyberboss: The Rise of Algorithmic Management | 2024 | Verso Books | **monograph** | low | curated_pure | default:no_signals |
| 2085 | Anime's Knowledge Cultures: Geek, Otaku, Zhai | 2024 | University of Minnes | **monograph** | low | curated_pure | default:no_signals |
| 2093 | The Politics and Ethics of Transhumanism: Tec | 2024 | Policy Press | **monograph** | low | curated_pure | default:no_signals |
| 2098 | Bateson’s Alphabet: The ABC's of Gregory Bate | 2024 | University of Michig | **monograph** | low | curated_pure | default:no_signals |
| 2207 | Patterns: Theory of the Digital Society | 2024 | Polity Press | **monograph** | low | curated_pure | default:no_signals |
| 2208 | The Riddle of Organismal Agency: New Historic | 2024 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2210 | Theory and Practice of Decision Making in Reg | 2024 | Taylor & Francis Lim | **monograph** | low | curated_pure | default:no_signals |
| 2211 | From Systems to Actor-Networks: A Paradigm Sh | 2024 | Ethics International | **monograph** | low | curated_pure | default:no_signals |
| 2243 | Cybernetic Revolution and Global Aging: Human | 2024 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer |
| 2247 | Organic Modernism: From the British Bauhaus t | 2024 | Bloomsbury Academic | **monograph** | low | title_corroborated | default:no_signals |
| 2251 | Powers of Perceptual Control, Volume I: An In | 2024 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 2264 | Relational Improvisation: Music, Dance and Co | 2024 | Routledge, Taylor &  | **monograph** | low | curated_keyword | default:no_signals |
| 2266 | Christian Eschatology of Artificial Intellige | 2024 | Becoming Press | **monograph** | low | title_corroborated | default:no_signals |
| 2268 | Machine and Sovereignty: For a Planetary Thin | 2024 | U of Minnesota Press | **monograph** | low | curated_pure | default:no_signals |
| 2275 | Music, the Avant-Garde, and Counterculture: I | 2024 | Springer Nature Swit | **monograph** | medium | curated_pure | publisher:springer |
| 2281 | Cybernetic Avatar | 2024 | Springer Nature Sing | **monograph** | medium | title_corroborated | publisher:springer |
| 2292 | Critical Systems Thinking: A Practitioner's G | 2024 | John Wiley & Sons | **monograph** | low | curated_pure | default:no_signals |
| 2296 | Truth Is the Invention of a Liar: Conversatio | 2024 | Carl-Auer Verlag | **monograph** | low | curated_keyword | default:no_signals |
| 2307 | Cybernetics and the Constructed Environment:  | 2024 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 2309 | Cybernetics of Art: Reason and the Rainbow | 2024 | Routledge, Chapman & | **monograph** | low | title_corroborated | default:no_signals |
| 2331 | The Cybernetic Border: Drones, Technology, an | 2024 | Duke University Pres | **monograph** | low | title_corroborated | default:no_signals |
| 2348 | The Brain Abstracted: Simplification in the H | 2024 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 2572 | Unconscious Intelligence in Cybernetic Psycho | 2024 | Routledge, Taylor &  | **monograph** | low | title_corroborated | default:no_signals |
| 2047 | The Composer's Black Box: Making Music in Cyb | 2025 | University of Califo | **monograph** | low | title_corroborated | default:no_signals |
| 2059 | Concrete Encoded: Poetry, Design, and the Cyb | 2025 | University of Texas  | **monograph** | low | title_corroborated | default:no_signals |
| 2060 | Acting With the World: Agency in the Anthropo | 2025 | Duke University Pres | **monograph** | low | curated_pure | default:no_signals |
| 2076 | Reading Talcott Parsons: A Re-Assessment of H | 2025 | Taylor & Francis Gro | **monograph** | low | curated_pure | default:no_signals |
| 2084 | Through the Screen: Towards a General Philoso | 2025 | De Gruyter | **monograph** | low | curated_keyword | default:no_signals |
| 2086 | Creative Work and Distributions of Power | 2025 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 2088 | Behaviourist Art and Cybernetics: Mapping a F | 2025 | Routledge, Chapman & | **monograph** | low | title_corroborated | default:no_signals |
| 2096 | The Ethics of AI: Power, Critique, Responsibi | 2025 | Policy Press | **monograph** | low | curated_pure | default:no_signals |
| 2097 | The Mathematical Theory of Semantic Communica | 2025 | Springer Nature Sing | **monograph** | medium | curated_pure | publisher:springer |
| 2121 | Bacteria to AI: Human Futures With Our Nonhum | 2025 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 2201 | Unifying Systems: Information, Feedback, and  | 2025 | Springer Nature Swit | **monograph** | medium | curated_pure | publisher:springer |
| 2216 | Utopia in the Factory: Prefigurative Knowledg | 2025 | Springer Nature Swit | **monograph** | medium | title_corroborated | publisher:springer |
| 2269 | Cybernetic Circulation Complex: Big Tech and  | 2025 | Verso Books | **monograph** | low | title_corroborated | default:no_signals |
| 2282 | Cybernetic Capitalism: A Critical Theory of t | 2025 | Fordham Univ Press | **monograph** | low | title_corroborated | default:no_signals |
| 2773 | Kant Machine: Critical Philosophy After AI | 2025 | Bloomsbury Publishin | **monograph** | low | curated_pure | default:no_signals |
| 2045 | Molecular Robotics II: Toward Chemical AI | 2026 | Springer Nature Sing | **monograph** | medium | curated_keyword | publisher:springer |
| 2775 | Cybernetic Imaginations | 2026 | Peter Lang AG Intern | **monograph** | low | title_corroborated | default:no_signals |
| 2192 | Progress in Biocybernetics: Volume 1 | 1964 |  | **anthology** | high | title_corroborated | title:volume_N, title:series_volume |
| 2193 | Progress in Biocybernetics: Volume 2 | 1965 | Elsevier | **anthology** | high | title_corroborated | title:volume_N, title:series_volume |
| 2110 | Collected Papers of Jay W. Forrester | 1975 | Productivity Press | **anthology** | high | curated_pure | title:collected |
| 2185 | About Bateson: Essays on Gregory Bateson | 1977 | Dutton | **anthology** | high | curated_pure | title:essays_on |
| 2326 | Sociocybernetics: An Actor-Oriented Social Sy | 1978 | Springer US | **anthology** | high | title_corroborated | title:vol_N, title:series_volume, publisher:springer |
| 2327 | Sociocybernetics. An Actor-Oriented Social Sy | 1978 | Springer | **anthology** | high | title_corroborated | title:volume_N, title:series_volume, publisher:springer |
| 2706 | Steps to an Ecology of Mind: Collected Essays | 1987 | Aronson | **anthology** | high | curated_pure | title:essays_on, title:collected |
| 2178 | The Individual, Communication, and Society: E | 1989 | Cambridge University | **anthology** | high | curated_pure | title:essays_on |
| 2361 | Essays on Self-Reference | 1990 | Columbia University  | **anthology** | high | curated_pure | title:essays_on |
| 2541 | Norbert Wiener, 1894-1964 | 1990 | Springer | **anthology** | medium | curated_keyword | publisher:springer, desc:contributors |
| 2416 | How Many Grapes Went Into the Wine: Stafford  | 1994 | Wiley | **anthology** | high | curated_pure | desc:edited_by |
| 2444 | Signs of Meaning in the Universe | 1996 | Indiana University P | **anthology** | medium | curated_pure | desc:contributors |
| 2120 | Essays on Life Itself | 1999 | Columbia University  | **anthology** | high | curated_pure | title:essays_on |
| 2760 | Understanding Understanding: Essays on Cybern | 2002 | Springer | **anthology** | high | title_corroborated | title:essays_on, publisher:springer, desc:contributors |
| 2483 | Kybernetes the International Journal of Syste | 2005 | Emerald Group Publis | **anthology** | medium | title_only | title:series_volume |
| 2397 | Purpose, Meaning, and Action: Control Systems | 2007 | Palgrave Macmillan U | **anthology** | medium | curated_pure | desc:contributors |
| 2232 | Systems Science and Cybernetics - Volume 2 | 2009 | EOLSS Publications | **anthology** | high | title_corroborated | title:volume_N, title:series_volume |
| 2233 | Systems Science and Cybernetics - Volume 1 | 2009 | EOLSS Publications | **anthology** | high | title_corroborated | title:volume_N, title:series_volume |
| 2645 | Emergence and Embodiment: New Essays on Secon | 2009 | Duke University Pres | **anthology** | high | curated_keyword | title:essays_on |
| 2711 | Systems Science and Cybernetics - Volume 3 | 2009 | EOLSS Publications | **anthology** | high | title_corroborated | title:volume_N, title:series_volume |
| 2222 | The Freudian Robot: Digital Media and the Fut | 2011 | University of Chicag | **anthology** | medium | curated_keyword | desc:contributors |
| 2234 | Fanged Noumena: Collected Writings 1987-2007 | 2011 | MIT Press | **anthology** | high | curated_pure | title:collected |
| 2577 | Adaptation and Well-Being: Social Allostasis | 2011 | Cambridge University | **anthology** | medium | curated_pure | desc:contributors |
| 2337 | When Things Go Wrong | 2012 | Routledge | **anthology** | high | curated_keyword | desc:edited_by |
| 2373 | Theory of Society, Volume 1 | 2012 | Stanford University  | **anthology** | high | curated_pure | title:volume_N, title:series_volume |
| 2583 | Allostasis, Homeostasis, and the Costs of Phy | 2012 | Cambridge University | **anthology** | high | curated_pure | desc:edited_by |
| 2336 | The Transhumanist Reader: Classical and Conte | 2013 | John Wiley & Sons | **anthology** | medium | curated_pure | title:essays_on, title:reader, desc:edited_by |
| 2372 | Theory of Society, Volume 2 | 2013 | Stanford University  | **anthology** | high | curated_pure | title:volume_N, title:series_volume |
| 2335 | Communication and Control: Tools, Systems, an | 2015 | Lexington Books | **anthology** | high | curated_keyword | desc:edited_by |
| 2438 | Anticipation Across Disciplines | 2015 | Springer | **anthology** | medium | curated_pure | publisher:springer, desc:contributors |
| 2751 | Systems, Cybernetics, Control, and Automation | 2017 | River Publishers | **anthology** | medium | title_corroborated | desc:contributors |
| 2600 | Beyond machines of loving grace: Hacker cultu | 2018 | Edições Sesc | **anthology** | high | title_only | desc:edited_by |
| 2420 | The Viability of Organizations Vol. 3: Design | 2019 | Springer Internation | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 2421 | The Viability of Organizations Vol. 2: Diagno | 2019 | Springer Internation | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 2422 | The Viability of Organizations Vol. 1: Decodi | 2019 | Springer Internation | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 2048 | Norbert Wiener - a Mathematician Among Engine | 2022 | World Scientific | **anthology** | medium | curated_keyword | desc:contributors |
| 2417 | Cybernetics and the Origin of Information | 2023 | Rowman & Littlefield | **anthology** | medium | title_corroborated | desc:contributors |
| 2332 | Cybernetics for the 21st Century Vol. 1: Epis | 2024 | Hanart Press | **anthology** | high | title_corroborated | title:vol_N, title:series_volume |
| 2356 | Engineering Cybernetics | 1954 | McGraw-Hill | **textbook** | medium | title_corroborated | publisher:textbook_house |
| 2419 | An Introduction to Information Theory: Symbol | 1961 | Dover Publications | **textbook** | medium | metadata_search | title:introduction_to |
| 2119 | Intelligent Machines: An Introduction to Cybe | 1962 | Blaisdell Publishing | **textbook** | medium | title_corroborated | title:introduction_to |
| 2143 | Man, Memory, and Machines: An Introduction to | 1964 | Macmillan | **textbook** | medium | title_corroborated | title:introduction_to |
| 2149 | Fundamentals of Engineering Cybernetics | 1965 | Israel Program for S | **textbook** | high | title_corroborated | title:fundamentals_of |
| 2140 | Introduction to Cybernetics | 1966 | Academic Press | **textbook** | medium | title_corroborated | title:introduction_to |
| 2271 | Cybernetic Principles of Learning and Educati | 1966 | Holt, Rinehart and W | **textbook** | medium | title_only | title:principles_of |
| 2519 | Introduction to Medical Cybernetics: By v. V. | 1967 | National Aeronautics | **textbook** | medium | title_only | title:introduction_to |
| 2288 | Principles of Systems | 1968 | Pegasus Communicatio | **textbook** | medium | curated_pure | title:principles_of |
| 2671 | Introduction to Economic Cybernetics | 1970 | Elsevier | **textbook** | medium | title_corroborated | title:introduction_to |
| 2529 | The Metaphorical Brain: An Introduction to Cy | 1972 | Wiley-Interscience | **textbook** | medium | title_corroborated | title:introduction_to |
| 2148 | The Anatomy of Business: An Introduction to B | 1974 | Wiley | **textbook** | medium | title_corroborated | title:introduction_to |
| 2123 | On the Texture of Brains: An Introduction to  | 1977 | Springer-Verlag | **textbook** | medium | title_corroborated | title:introduction_to, publisher:springer |
| 2434 | Living Systems | 1978 | McGraw-Hill | **textbook** | medium | curated_pure | publisher:textbook_house |
| 2342 | Principles of Biological Autonomy | 1979 | North Holland | **textbook** | medium | curated_pure | title:principles_of |
| 2707 | Subjectivity, Information, Systems: Introduct | 1986 | Routledge | **textbook** | medium | title_only | title:introduction_to |
| 2049 | Management Systems: Conceptual Considerations | 1990 | McGraw-Hill Higher E | **textbook** | medium | curated_pure | publisher:textbook_house |
| 2408 | Introduction to Modern Psychology: The Contro | 1990 | Control Systems Grou | **textbook** | medium | curated_pure | title:introduction_to |
| 2724 | The Evolution of Ethics: An Introduction to C | 1999 | Dianic Publications | **textbook** | medium | title_corroborated | title:introduction_to |
| 2531 | Facets of Systems Science | 2001 | Springer Science & B | **textbook** | high | curated_keyword | publisher:springer, desc:intro_text |
| 2270 | Organizations as Complex Systems: An Introduc | 2006 | IAP | **textbook** | medium | title_only | title:introduction_to |
| 2589 | An Introduction to Systems Biology: Design Pr | 2006 | CRC Press | **textbook** | high | curated_pure | title:introduction_to, title:principles_of |
| 2370 | Change: Principles of Problem Formation and P | 2011 | W. W. Norton & Compa | **textbook** | high | curated_pure | title:principles_of, publisher:textbook_house |
| 2371 | Pragmatics of Human Communication: A Study of | 2011 | W. W. Norton & Compa | **textbook** | medium | curated_pure | publisher:textbook_house |
| 2328 | Fundamentals of Cybernetics | 2012 | Springer US, Boston, | **textbook** | high | title_only | title:fundamentals_of, publisher:springer |
| 2365 | Introduction to Systems Theory | 2013 | Polity | **textbook** | medium | curated_pure | title:introduction_to |
| 2667 | An Introduction to Cybernetics | 2015 | Martino Publishing | **textbook** | medium | title_corroborated | title:introduction_to |
| 2692 | Principles of Neural Design | 2015 | MIT Press | **textbook** | medium | curated_pure | title:principles_of |
| 2302 | Rise of the Machines: A Cybernetic History | 2016 | W. W. Norton & Compa | **textbook** | medium | title_corroborated | publisher:textbook_house |
| 2459 | Introduction to Anticipation Studies | 2017 | Springer | **textbook** | medium | curated_pure | title:introduction_to, publisher:springer |
| 2606 | Content Analysis: An Introduction to Its Meth | 2018 | SAGE Publications | **textbook** | medium | metadata_search | title:introduction_to |
| 2203 | Introduction to Systems Philosophy: Toward a  | 2021 | Taylor & Francis Gro | **textbook** | medium | curated_pure | title:introduction_to |
| 2329 | Introduction to Cybersemiotics: A Transdiscip | 2021 | Springer Internation | **textbook** | medium | curated_keyword | title:introduction_to, publisher:springer |
| 2362 | Unlocking Luhmann: A Keyword Introduction to  | 2021 | Bielefeld University | **textbook** | medium | curated_pure | title:introduction_to |
| 2553 | An Introduction to Cybernetic Synergy: Improv | 2021 | Taylor & Francis Lim | **textbook** | medium | title_corroborated | title:introduction_to |
| 2468 | Ingenious Principles of Nature: Do We Reckon  | 2022 | Springer Fachmedien  | **textbook** | medium | curated_keyword | title:principles_of, publisher:springer |
| 2491 | Introduction to Safety Science: People, Organ | 2022 | CRC Press | **textbook** | medium | curated_pure | title:introduction_to |
| 2593 | A Transdisciplinary Introduction to the World | 2023 | Springer Fachmedien  | **textbook** | medium | title_corroborated | title:introduction_to, publisher:springer |
| 2102 | Minds and Machines | 1954 | Penguin Books | **popular** | medium | curated_keyword | publisher:trade_house |
| 2103 | The Communication Systems of the Body | 1964 | Basic Books | **popular** | medium | curated_keyword | publisher:trade_house |
| 2512 | Management Science: The Business Use of Opera | 1968 | Doubleday | **popular** | medium | curated_keyword | publisher:trade_house |
| 2696 | Psycho-Cybernetics | 1969 | Pocket Books | **popular** | high | title_only | title:psycho_cyber |
| 2118 | How to Use the Magic of Self-Cybernetics | 1974 | Littlefield, Adams | **popular** | medium | title_only | title:how_to |
| 2547 | II Cybernetic Frontiers | 1974 | Random House | **popular** | medium | title_corroborated | publisher:trade_house |
| 2303 | Hypno Cybernetics: Helping Yourself to a Rich | 1976 | Penguin Group (USA)  | **popular** | high | title_only | title:rich_life, publisher:trade_house |
| 2369 | How Real Is Real?: Confusion, Disinformation, | 1976 | Random House | **popular** | medium | curated_pure | publisher:trade_house |
| 2508 | Whole Earth Software Catalog 1986 | 1985 | Anchor | **popular** | medium | curated_pure | publisher:trade_house |
| 2585 | Angels Fear: Towards an Epistemology of the S | 1988 | Bantam | **popular** | medium | curated_pure | publisher:trade_house |
| 2144 | Structural Cybernetics: An Overview, How to B | 1995 | N. Dean Myer and Ass | **popular** | medium | title_corroborated | title:how_to |
| 2509 | How Buildings Learn: What Happens After They' | 1995 | Penguin Books | **popular** | medium | curated_pure | publisher:trade_house |
| 2391 | The Age of Spiritual Machines | 1998 | Penguin | **popular** | medium | curated_pure | publisher:trade_house |
| 2298 | Full Circles Overlapping Lives: Culture and G | 2000 | Random House | **popular** | medium | curated_pure | publisher:trade_house |
| 2703 | R.U.R. (Rossum's Universal Robots) | 2004 | Penguin | **popular** | medium | curated_pure | publisher:trade_house |
| 2392 | The Singularity Is Near: When Humans Transcen | 2005 | Penguin Books | **popular** | medium | curated_pure | publisher:trade_house |
| 2404 | The Method of Levels: How to Do Psychotherapy | 2006 | Living Control Syste | **popular** | medium | curated_pure | title:how_to |
| 2507 | The Clock of the Long Now: Time and Responsib | 2008 | Basic Books | **popular** | medium | curated_pure | publisher:trade_house |
| 2637 | Dark Hero of the Information Age: In Search o | 2009 | Basic Books | **popular** | medium | title_corroborated | publisher:trade_house |
| 2300 | Composing a Further Life: The Age of Active W | 2010 | Knopf Doubleday Publ | **popular** | medium | curated_pure | publisher:trade_house, desc:contributors |
| 2510 | Whole Earth Discipline: Why Dense Cities, Nuc | 2010 | Penguin Publishing G | **popular** | medium | curated_pure | publisher:trade_house |
| 2725 | The Information: A History, a Theory, a Flood | 2011 | Knopf Doubleday Publ | **popular** | medium | curated_pure | publisher:trade_house |
| 2390 | How to Create a Mind: The Secret of Human Tho | 2012 | Viking | **popular** | medium | curated_pure | title:how_to |
| 2768 | Psycho-Cybernetics and Self-Fulfillment | 2013 | Igal Meirovich | **popular** | high | title_corroborated | title:psycho_cyber, desc:self_help |
| 2565 | Psycho-Cybernetics: Updated and Expanded | 2015 | Penguin | **popular** | high | title_corroborated | title:psycho_cyber, publisher:trade_house, desc:self_help |
| 2685 | Our Robots, Ourselves: Robotics and the Myths | 2015 | Penguin | **popular** | medium | curated_pure | publisher:trade_house |
| 2628 | Ranulph Galnville and How to Live the Cyberne | 2016 |  | **popular** | medium | title_corroborated | title:how_to |
| 2772 | Sonic Intimacy: Voice, Species, Technics (Or, | 2017 | Stanford University  | **popular** | medium | curated_keyword | title:how_to |
| 2691 | Possible Minds: Twenty-Five Ways of Looking a | 2019 | Penguin Press | **popular** | medium | curated_keyword | publisher:trade_house |
| 2410 | A Foundational Explanation of Human Behavior: | 2021 | Amazon Digital Servi | **popular** | medium | curated_pure | title:how_to |
| 2273 | Repair: When and How to Improve Broken Object | 2022 | Springer Internation | **popular** | medium | curated_pure | title:how_to, publisher:springer |
| 2709 | Success Cybernetics (Unabridged Edition) | 2022 | David De Angelis | **popular** | medium | title_corroborated | title:success |
| 2079 | The Atomic Human: Understanding Ourselves in  | 2024 | Random House | **popular** | medium | curated_pure | publisher:trade_house |
| 2274 | Feedback: How to Destroy or Save the World | 2024 | Springer Nature | **popular** | medium | curated_pure | title:how_to, publisher:springer |
| 2285 | The Singularity Is Nearer: When We Merge With | 2024 | Penguin Publishing G | **popular** | medium | curated_pure | publisher:trade_house |
| 2087 | Psycho-Cybernetics 365: Thrive and Grow Every | 2025 | St. Martin's Publish | **popular** | high | title_corroborated | title:psycho_cyber |
| 2215 | The Cybernetic Society: How Humans and Machin | 2025 | Basic Books | **popular** | medium | title_corroborated | publisher:trade_house |
| 2230 | Posthumanism Meets Surveillance Capitalism: H | 2025 | Springer Nature Swit | **popular** | medium | curated_pure | title:how_to, publisher:springer |
| 2439 | Gregory Bateson: The Legacy of a Scientist | 1982 | Beacon Press | **history_bio** | high | curated_pure | title:legacy_of, desc:biography |
| 2297 | With a Daughter's Eye: A Memoir of Margaret M | 1984 | W. Morrow | **history_bio** | high | curated_pure | title:memoir, desc:memoir |
| 2718 | The Cybernetics Group | 1991 | MIT Press | **history_bio** | high | title_corroborated | desc:biography |
| 2653 | From Newspeak to Cyberspeak: A History of Sov | 2002 | MIT Press | **history_bio** | high | title_corroborated | title:history_of |
| 2415 | Stafford Beer: A Personal Memoir - Includes a | 2003 | Wavestone Press | **history_bio** | high | curated_keyword | title:memoir |
| 2448 | Digital Performance: A History of New Media i | 2007 | MIT Press | **history_bio** | high | curated_pure | title:history_of |
| 2256 | Biosemiotics: An Examination Into the Signs o | 2008 | University of Scrant | **history_bio** | high | curated_pure | title:life_of |
| 2739 | Understanding Gregory Bateson: Mind, Beauty,  | 2008 | SUNY Press | **history_bio** | high | curated_keyword | desc:biography |
| 2246 | Systems Thinkers | 2009 | Springer London | **history_bio** | high | curated_pure | publisher:springer, desc:biography |
| 2115 | Introduction to the History of Communication: | 2010 | Peter Lang | **history_bio** | medium | curated_keyword | title:introduction_to, title:history_of |
| 2195 | Beautiful Data: A History of Vision and Reaso | 2015 | Duke University Pres | **history_bio** | high | curated_keyword | title:history_of |
| 2398 | Cybernethisms: Aldo Giorgini's Computer Art L | 2015 | Purdue University Pr | **history_bio** | high | curated_pure | desc:biography |
| 2340 | Staying With the Trouble: Making Kin in the C | 2016 | Duke University Pres | **history_bio** | high | curated_pure | desc:biography, desc:memoir |
| 2661 | How Not to Network a Nation: The Uneasy Histo | 2016 | MIT Press | **history_bio** | high | curated_keyword | title:history_of |
| 2759 | Upside-Down Gods: Gregory Bateson's World of  | 2016 | Fordham Univ Press | **history_bio** | high | curated_pure | desc:biography |
| 2568 | Runaway: Gregory Bateson, the Double Bind, an | 2017 | University of North  | **history_bio** | high | curated_pure | desc:biography |
| 2655 | Harmonies of Disorder: Norbert Wiener: A Math | 2017 | Springer Internation | **history_bio** | high | curated_keyword | publisher:springer, desc:biography |
| 2658 | How Emotions Are Made: The Secret Life of the | 2017 | Houghton Mifflin Har | **history_bio** | high | curated_pure | title:life_of |
| 2677 | Norbert Wiener-A Life in Cybernetics: Ex-Prod | 2018 | MIT Press | **history_bio** | high | title_corroborated | title:life_of |
| 2068 | Communication Theory Through the Ages | 2019 | Routledge | **history_bio** | high | curated_pure | desc:biography |
| 2657 | History of Computer Art | 2020 | Lulu Press, Incorpor | **history_bio** | high | curated_keyword | title:history_of |
| 2279 | Whole Earth: The Many Lives of Stewart Brand | 2022 | Penguin Publishing G | **history_bio** | medium | curated_pure | publisher:trade_house, desc:biography |
| 2212 | A History of Artificially Intelligent Archite | 2023 | Routledge/Taylor & F | **history_bio** | high | curated_keyword | title:history_of |
| 2333 | Return to China One Day: The Learning Life of | 2023 | Springer | **history_bio** | high | curated_pure | title:life_of, publisher:springer |
| 2456 | The Eye of the Master: A Social History of Ar | 2023 | Verso | **history_bio** | high | curated_pure | title:history_of |
| 2238 | An Artificial History of Natural Intelligence | 2024 | University of Chicag | **history_bio** | high | curated_pure | title:history_of |
| 2317 | The Unaccountability Machine | 2024 | Profile Books Limite | **history_bio** | high | curated_keyword | desc:biography |
| 2083 | Burning Down the House: Talking Heads and the | 2025 | HarperCollins Publis | **history_bio** | medium | curated_pure | desc:contributors, desc:biography |
| 2353 | The Way Things Work Book of the Computer: An  | 1974 | Simon and Schuster | **handbook** | high | title_corroborated | title:encyclopedia |
| 2748 | International Encyclopedia of Systems and Cyb | 1997 | K.G. Saur | **handbook** | high | title_corroborated | title:encyclopedia |
| 2338 | Handbook of Personality and Self-Regulation | 2010 | Wiley-Blackwell | **handbook** | high | curated_pure | title:handbook |
| 2399 | International Handbook of Semiotics | 2015 | Springer | **handbook** | high | curated_pure | title:handbook, publisher:springer |
| 2734 | The Routledge Handbook of Philosophy of Infor | 2016 | Routledge, Taylor &  | **handbook** | high | curated_pure | title:handbook |
| 2209 | The Routledge Handbook of Soft Power | 2017 | Routledge | **handbook** | high | curated_pure | title:handbook |
| 2656 | Handbook of Research on Applied Cybernetics a | 2017 | IGI Global | **handbook** | high | title_corroborated | title:handbook |
| 2074 | A Silvan Tomkins Handbook: Foundations for Af | 2020 | University of Minnes | **handbook** | high | curated_pure | title:handbook |
| 2654 | Handbook of Anticipation: Theoretical and App | 2020 | Springer Internation | **handbook** | high | curated_pure | title:handbook, publisher:springer |
| 2755 | The Interdisciplinary Handbook of Perceptual  | 2020 | Elsevier Science | **handbook** | medium | curated_pure | title:handbook, desc:biography |
| 2426 | Handbook of Systems Sciences | 2021 | Springer Nature Sing | **handbook** | high | curated_pure | title:handbook, publisher:springer |
| 2276 | The Sage Handbook of Human-Machine Communicat | 2023 | SAGE | **handbook** | high | curated_pure | title:handbook |
| 2237 | Handbook of Emotion Regulation | 2024 | Guilford Publication | **handbook** | high | curated_pure | title:handbook |
| 2615 | Current Topics in Cybernetics and Systems: Pr | 1978 | Springer | **proceedings** | high | title_only | title:proceedings, publisher:springer |
| 2170 | Science of Goal Formulation | 1990 | CRC Press | **proceedings** | high | curated_keyword | desc:proceedings |
| 2684 | Our Own Metaphor: A Personal Account of a Con | 2004 | Hampton Pr | **proceedings** | high | curated_pure | title:conference_on |
| 2587 | Anticipatory Behavior in Adaptive Learning Sy | 2009 | Springer | **proceedings** | high | curated_pure | publisher:springer, desc:proceedings |
| 2535 | Cybernetics and Systems ’86: Proceedings of t | 2011 | Springer | **proceedings** | high | title_corroborated | title:proceedings, publisher:springer, desc:proceedings |
| 2245 | Systems Thinking in Europe | 2012 | Springer US | **proceedings** | high | metadata_search | publisher:springer, desc:proceedings |
| 2458 | Anticipation, Agency and Complexity | 2019 | Springer | **proceedings** | high | curated_pure | publisher:springer, desc:proceedings |
| 2213 | Russian-English dictionary and reader in the  | 1966 | Academic Press | **reader** | medium | title_only | title:reader, title:bibliography |
| 2409 | Living Control Systems: Selected Papers of Wi | 1989 | Control Systems Grou | **reader** | high | curated_pure | title:selected |
| 2190 | Living Control Systems II: Selected Papers of | 1992 |  | **reader** | high | curated_pure | title:selected |
| 2465 | A Stanislaw Lem Reader | 1997 | Northwestern Univers | **reader** | high | curated_pure | title:reader |
| 2747 | Information: A Reader | 2022 | Columbia University  | **reader** | high | curated_pure | title:reader |
| 2058 | Basic and Applied General Systems Research: A | 1985 | Hemisphere Publishin | **report** | high | curated_pure | title:bibliography |