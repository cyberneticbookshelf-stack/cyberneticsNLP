# Book Style Classification

**Date:** 2026-04-02  
**Corpus:** 726 books  
**Input:** csv/books_metadata_full.csv  
**Method:** Heuristic signal matching — title, author, publisher, description, tags  

## Summary

| Style | Count | % |
|---|---|---|
| monograph | 517 | 71.2% |
| textbook | 57 | 7.9% |
| popular | 47 | 6.5% |
| anthology | 47 | 6.5% |
| history_bio | 27 | 3.7% |
| handbook | 12 | 1.7% |
| proceedings | 12 | 1.7% |
| reader | 5 | 0.7% |
| report | 2 | 0.3% |

## Inclusion Strata

| Stratum | Count | % |
|---|---|---|
| curated_pure | 330 | 45.5% |
| title_corroborated | 183 | 25.2% |
| curated_keyword | 144 | 19.8% |
| title_only | 55 | 7.6% |
| metadata_search | 14 | 1.9% |

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
| 432 | Cybernetika 1.0 | 0101 |  | **monograph** | low | curated_pure | default:no_signals |
| 918 | Stosunek Filozofii Do Cybernetyki Czyli Sztuk | 1843 |  | **monograph** | low | curated_pure | default:no_signals |
| 1778 | Balinese Character: A Photographic Analysis | 1942 | New York academy of  | **monograph** | low | curated_pure | default:no_signals |
| 1949 | The Next Step in Management: An Appraisal of  | 1952 |  | **monograph** | low | title_only | default:no_signals |
| 1720 | Cybernetics: Circular, Causal and Feedback Me | 1953 | Macy Foundation | **monograph** | low | title_corroborated | default:no_signals |
| 1215 | The Computer and the Brain | 1957 | Yale University Pres | **monograph** | low | curated_keyword | default:no_signals |
| 1895 | The Origins of Life | 1957 | Creative Media Partn | **monograph** | low | curated_keyword | default:no_signals |
| 1839 | Communication, Organization, and Science | 1958 | Falcon's Wing Press | **monograph** | low | curated_keyword | default:no_signals |
| 178 | What Is Cybernetics? | 1959 | Criterion Books | **monograph** | low | title_only | default:no_signals |
| 1848 | Automation, Cybernetics, and Society | 1959 | L. Hill | **monograph** | low | title_corroborated | default:no_signals |
| 1113 | Design for a Brain | 1960 | Springer Netherlands | **monograph** | medium | curated_pure | publisher:springer, primo:type_web_resource |
| 1827 | Random Wavelets and Cybernetic Systems | 1962 | CHARLES GRIFFIN & CO | **monograph** | low | title_only | default:no_signals |
| 1700 | The Nerves of Government: Models of Political | 1963 | Free Press of Glenco | **monograph** | low | curated_keyword | default:no_signals |
| 1773 | Nerve, Brain and Memory Models | 1963 | Elsevier | **monograph** | low | curated_pure | default:no_signals |
| 1898 | Cybernetics | 1963 | Hawthorn Books | **monograph** | low | title_corroborated | default:no_signals |
| 1518 | Industrial Dynamics | 1964 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 1840 | Cybernation and Social Change | 1964 | U.S. Department of L | **monograph** | low | curated_keyword | default:no_signals |
| 329 | Cybernetics of the Nervous System | 1965 | Elsevier | **monograph** | low | title_corroborated | default:no_signals |
| 1808 | Cybernetic Medicine | 1965 | C. C. Thomas | **monograph** | low | title_corroborated | default:no_signals |
| 1820 | Cybernetics and Biology | 1965 | W. H. Freeman | **monograph** | low | title_corroborated | default:no_signals |
| 1847 | Wholes and Parts: A General Theory of System  | 1965 | Pergamon Press | **monograph** | low | curated_keyword | default:no_signals |
| 1868 | Biological Rhythm Research | 1965 | Elsevier Publishing  | **monograph** | low | curated_keyword | default:no_signals |
| 415 | God & Golem, Inc.: A Comment on Certain Point | 1966 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 1811 | Cybernetic Modelling | 1966 | Wliffe Books Ltd. | **monograph** | low | title_corroborated | default:no_signals |
| 1824 | Great Ideas in Information Theory, Language a | 1966 | Dover Publications | **monograph** | low | title_corroborated | default:no_signals |
| 1897 | Structure, Form, Movement | 1966 | Reinhold | **monograph** | low | curated_keyword | default:no_signals |
| 1455 | Whole Earth Catalog Access to Tools | 1967 |  | **monograph** | low | curated_pure | default:no_signals |
| 1717 | The Science of Art: The Cybernetics of Creati | 1967 | John Day Company | **monograph** | low | title_corroborated | default:no_signals |
| 1719 | Philosophy and Cybernetics | 1967 | University of Notre  | **monograph** | low | title_corroborated | default:no_signals |
| 423 | An Approach to Cybernetics | 1968 | Hutchinson | **monograph** | low | title_corroborated | default:no_signals |
| 912 | La cybernétique et l'origine de l'information | 1968 | Flammarion | **monograph** | low | curated_pure | default:no_signals |
| 1612 | Cybernetic Serendipity: The Computer and the  | 1968 | Studio International | **monograph** | low | title_only | default:no_signals |
| 1814 | Key Papers in Cybernetics | 1968 | University Park Pres | **monograph** | low | title_corroborated | default:no_signals |
| 1819 | Cybernetics and the Image of Man: A Study of  | 1968 | Abingdon Press | **monograph** | low | title_corroborated | default:no_signals |
| 179 | The Social Impact of Cybernetics | 1969 | University of Notre  | **monograph** | low | title_only | default:no_signals |
| 212 | The Management Process, Management Informatio | 1969 | M.I.T. | **monograph** | low | title_corroborated | default:no_signals |
| 1416 | Information, Mechanism and Meaning | 1969 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 1815 | Cybernetics, Society, and the Church | 1969 | Pflaum Press | **monograph** | low | title_corroborated | default:no_signals |
| 1816 | Cybernetics Simplified | 1969 | English Universities | **monograph** | low | title_corroborated | default:no_signals |
| 1993 | Market Cybernetic Processes | 1969 | Almqvist & Wiksell | **monograph** | low | title_corroborated | default:no_signals |
| 208 | The Origins of Feedback Control | 1970 | M.I.T. Press | **monograph** | low | curated_keyword | default:no_signals |
| 1227 | You Are a Computer: Cybernetics in Everyday L | 1970 | Emerson Books | **monograph** | low | title_corroborated | default:no_signals |
| 1817 | Cybernetics in Management | 1970 | Pan Books | **monograph** | low | title_corroborated | default:no_signals |
| 1825 | Subduing the Cosmos: Cybernetics and Man's Fu | 1970 | John Knox Press | **monograph** | low | title_corroborated | default:no_signals |
| 1845 | Politics and Government: How People Decide Th | 1970 | Houghton Mifflin | **monograph** | low | curated_pure | default:no_signals |
| 1846 | Kybernetics of Mind and Brain | 1970 | Thomas | **monograph** | low | curated_keyword | default:no_signals |
| 290 | Information and Control in the Living Organis | 1971 | Chapman and Hall | **monograph** | low | curated_pure | default:no_signals |
| 682 | The Last Whole Earth Catalog: Access to Tools | 1971 | Portola Institute | **monograph** | low | curated_pure | default:no_signals |
| 1270 | Cybernetics, Art, and Ideas | 1971 | Graphie Society | **monograph** | low | title_only | default:no_signals |
| 1519 | World Dynamics | 1971 | Wright-Allen Press | **monograph** | low | curated_pure | default:no_signals |
| 1813 | Cybernetics | 1971 | St. Paul's House | **monograph** | low | title_corroborated | default:no_signals |
| 1966 | The Age of Information: An Interdisciplinary  | 1971 | Educational Technolo | **monograph** | low | title_corroborated | default:no_signals |
| 281 | Mathematical Structure of Finite Random Cyber | 1972 | Springer Vienna | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 284 | Laws of Form | 1972 | Julian Press | **monograph** | low | curated_pure | default:no_signals |
| 1806 | Cybernetic Aspects of Language | 1972 | Mouton | **monograph** | low | title_corroborated | default:no_signals |
| 1807 | Cybernetic Creativity | 1972 | R. Speller | **monograph** | low | title_corroborated | default:no_signals |
| 1843 | Theory and World Politics | 1972 | Winthrop | **monograph** | low | curated_pure | default:no_signals |
| 1962 | Grundbegriffe der Kybernetik: eine Einf | 1972 | Hirzel | **monograph** | low | curated_keyword | default:no_signals |
| 1122 | Birth & Death & Cybernation | 1973 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1718 | Cybernetic Engineering | 1973 | Butterworths | **monograph** | low | title_only | default:no_signals |
| 1835 | Cybernetic and Sculpture Environnement | 1973 | Galerie Denise René | **monograph** | low | title_only | default:no_signals |
| 1874 | Sexual Cybernetics | 1973 | Pinnacle Books | **monograph** | low | title_corroborated | default:no_signals |
| 1990 | Ecclesial Cybernetics: A Study of Democracy i | 1973 | Macmillan | **monograph** | low | title_corroborated | default:no_signals |
| 191 | Cybernetics a to Z | 1974 | Mir Publishers | **monograph** | low | title_corroborated | default:no_signals |
| 573 | The Cybernetic Revolution | 1974 | Barnes & Noble Books | **monograph** | low | title_corroborated | default:no_signals |
| 1019 | The Cyberiad; Fables for the Cybernetic Age | 1974 | Seabury Press | **monograph** | low | title_corroborated | default:no_signals |
| 1517 | The Cybernetic Theory of Development Mathemat | 1974 | Kustannusosakeyhtio  | **monograph** | low | title_only | default:no_signals |
| 183 | The Cybernetics of Human Learning and Perform | 1975 | Taylor & Francis Gro | **monograph** | low | title_corroborated | default:no_signals |
| 355 | Conversation, Cognition and Learning: A Cyber | 1975 | Elsevier | **monograph** | low | title_only | default:no_signals |
| 1834 | The Intelligent Universe: A Cybernetic Philos | 1975 | Putnam | **monograph** | low | title_corroborated | default:no_signals |
| 1892 | Cybernetic Approach to Stock Market Analysis, | 1975 | Exposition Press | **monograph** | low | title_corroborated | default:no_signals |
| 1995 | Engineering Cybernetics | 1975 | Prentice-Hall | **monograph** | low | title_corroborated | default:no_signals |
| 352 | Conversation Theory: Applications in Educatio | 1976 | Elsevier | **monograph** | low | curated_pure | default:no_signals |
| 571 | Mathematical Philosophy and Foundations: Pote | 1976 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1222 | Generalized Harmonic Analysis and Tauberian T | 1976 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1776 | Democracy at Work: The Report of the Norwegia | 1976 | Springer US | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1803 | Biological Machines: A Cybernetic Approach to | 1976 | Edward Arnold | **monograph** | low | title_corroborated | default:no_signals |
| 1812 | Cybernetic Methods in Chemistry & Chemical En | 1976 | Mir Publishers | **monograph** | low | title_corroborated | default:no_signals |
| 1994 | Instructional Regulation and Control: Cyberne | 1976 | Educational Technolo | **monograph** | low | title_corroborated | default:no_signals |
| 205 | The Phenomenon of Science | 1977 | Columbia Univ Pr | **monograph** | low | curated_keyword | default:no_signals |
| 364 | Computers and the Cybernetic Society | 1977 | Academic Press | **monograph** | low | title_corroborated | default:no_signals |
| 1727 | The Foundations of Cybernetics | 1977 | Gordon and Breach | **monograph** | low | title_corroborated | default:no_signals |
| 1742 | Systems Thinking: Concepts and Notions | 1977 | Martinus Nijhoff | **monograph** | low | curated_pure | default:no_signals |
| 1961 | Socialisme et cybernétique | 1977 | Calmann-Lévy | **monograph** | low | curated_keyword | default:no_signals |
| 1802 | Applied Cybernetics: Its Relevance in Operati | 1978 | Gordon and Breach | **monograph** | low | title_corroborated | default:no_signals |
| 1836 | The Stable Society: Its Structure and Control | 1978 | Wadebridge Press | **monograph** | low | title_only | default:no_signals |
| 261 | Philosophical Foundations of Cybernetics | 1979 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 277 | Mind and Nature: A Necessary Unity | 1979 | Dutton | **monograph** | low | curated_pure | default:no_signals |
| 1886 | Urban Dynamics | 1979 | M.I.T. Press | **monograph** | low | curated_pure | default:no_signals |
| 188 | John Von Neumann and Norbert Wiener: From Mat | 1980 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 376 | Autopoiesis and Cognition: The Realization of | 1980 | D. Reidel Publishing | **monograph** | low | curated_pure | default:no_signals |
| 434 | Economic Cybernetics | 1980 | Abacus Press | **monograph** | low | title_corroborated | default:no_signals |
| 575 | The Cybernetic Imagination in Science Fiction | 1980 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 1883 | System Dynamics | 1980 | North-Holland Publis | **monograph** | low | curated_pure | default:no_signals |
| 287 | Mechanisms of Intelligence: Ashby's Writings  | 1981 | Intersystems Publica | **monograph** | low | title_corroborated | default:no_signals |
| 360 | Control and Ability: Towards a Biocybernetics | 1981 | John Benjamins Publi | **monograph** | low | curated_keyword | default:no_signals |
| 431 | The Creation of Life: A Cybernetic Approach t | 1981 | Master Books | **monograph** | low | title_corroborated | default:no_signals |
| 1223 | The Hopf-Wiener Integral Equation: Prediction | 1981 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1818 | Cybernetics and Society: An Analysis of Socia | 1981 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 1959 | Saggi sulla cibernetica | 1981 | EDINT | **monograph** | low | curated_keyword | default:no_signals |
| 325 | Cybernetics Within Us | 1982 | Wilshire Book Compan | **monograph** | low | title_only | default:no_signals |
| 370 | Biological Foundations of Linguistic Communic | 1982 | John Benjamins Publi | **monograph** | low | curated_pure | default:no_signals |
| 228 | The Cybernetic Foundation Mathematics | 1983 | The City University  | **monograph** | low | title_only | default:no_signals |
| 428 | A Cybernetic Approach to Colour Perception | 1983 | Gordon and Breach Sc | **monograph** | low | title_corroborated | default:no_signals |
| 444 | Cybernetics, Theory and Applications | 1983 | Hemisphere Pub | **monograph** | low | title_only | default:no_signals |
| 1183 | The Tree of Knowledge: The Biological Roots o | 1983 | Shambhala | **monograph** | low | curated_pure | default:no_signals |
| 1734 | Aesthetics of Change | 1983 | Guilford Publication | **monograph** | low | curated_keyword | default:no_signals |
| 1800 | Management Principles and Practice: A Cyberne | 1983 | Gordon and Breach Sc | **monograph** | low | title_corroborated | default:no_signals |
| 184 | Observing Systems | 1984 | Intersystems Publica | **monograph** | low | curated_keyword | default:no_signals |
| 569 | The Science of History: A Cybernetic Approach | 1984 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 1264 | Cybernetics, Science, and Society; Ethics, Ae | 1985 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 1810 | Cybernetic Music | 1985 | Tab Books | **monograph** | low | title_corroborated | default:no_signals |
| 260 | Power, Autonomy, Utopia: New Approaches Towar | 1986 | Springer | **monograph** | medium | curated_keyword | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 439 | Beyond Mechanization: Work and Technology in  | 1986 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 670 | Pebbles to Computers: The Thread | 1986 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 1453 | The Control Revolution: Technological and Eco | 1986 | Harvard University P | **monograph** | low | curated_pure | default:no_signals |
| 1725 | Cybernetic Medley | 1986 | Mir Publishers Mosco | **monograph** | low | title_corroborated | default:no_signals |
| 1830 | Organizational Cybernetics and Business Polic | 1986 | Pennsylvania State U | **monograph** | low | title_corroborated | default:no_signals |
| 211 | The Media Lab: Inventing the Future at MIT | 1987 | Viking | **monograph** | low | curated_pure | default:no_signals |
| 572 | Brains, Machines, and Mathematics | 1987 | Springer Verlag | **monograph** | medium | curated_keyword | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1123 | Art in the Science Dominated World: Science,  | 1987 | Taylor & Francis | **monograph** | low | curated_keyword | default:no_signals |
| 214 | The Human Use of Human Beings: Cybernetics an | 1989 | Free Association | **monograph** | low | title_corroborated | default:no_signals |
| 1262 | Ecological Communication | 1989 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 1805 | Computers, Automation, and Cybernetics at the | 1989 | The Museum | **monograph** | low | title_corroborated | default:no_signals |
| 250 | Self-Steering and Cognition in Complex System | 1990 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 1214 | The Age of Intelligent Machines | 1990 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1768 | Biological Feedback | 1990 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 275 | New Perspectives on Cybernetics: Self-Organiz | 1991 | Springer | **monograph** | medium | title_corroborated | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 314 | Feedback Thought in Social Science and System | 1991 | University of Pennsy | **monograph** | low | curated_pure | default:no_signals |
| 379 | A Sacred Unity: Further Steps to an Ecology o | 1991 | Cornelia & Michael B | **monograph** | low | curated_pure | default:no_signals |
| 681 | Life Itself: A Comprehensive Inquiry Into the | 1991 | Columbia University  | **monograph** | low | curated_pure | default:no_signals |
| 743 | Simians, Cyborgs and Women: The Reinvention o | 1991 | Free Association Boo | **monograph** | low | curated_keyword | default:no_signals |
| 1034 | Radical Constructivism in Mathematics Educati | 1991 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1781 | A Cyborg Manifesto | 1991 |  | **monograph** | low | curated_keyword | default:no_signals |
| 1809 | Cybernetics: A New Management Tool | 1991 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 243 | Sociocybernetics: A Perspective for Living in | 1992 | Social Systems Press | **monograph** | low | curated_keyword | default:no_signals |
| 317 | Designing Freedom | 1993 | House of Anansi | **monograph** | low | curated_keyword | default:no_signals |
| 1821 | Cybernetics in Water Resources Management | 1993 | Water Resources Publ | **monograph** | low | title_corroborated | default:no_signals |
| 1829 | Organisational Fitness: Corporate Effectivene | 1993 | Campus Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 1875 | Systemic Psychotherapy With Families, Couples | 1993 | Jason Aronson | **monograph** | low | curated_pure | default:no_signals |
| 668 | Invention: The Care and Feeding of Ideas | 1994 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 770 | The Cybernetics of Prejudices in the Practice | 1994 | Karnac Books | **monograph** | low | title_only | default:no_signals |
| 1804 | Biological Psychology: A Cybernetic Science | 1994 | Prentice Hall | **monograph** | low | title_corroborated | default:no_signals |
| 1849 | Cyberia: Life in the Trenches of Hyperspace | 1994 | Flamingo | **monograph** | low | curated_keyword | default:no_signals |
| 1960 | Etica y cibernética: ensayos filosóficos | 1994 | Monte Avila Editores | **monograph** | low | curated_keyword | default:no_signals |
| 570 | Reasoning Into Reality: A System-Cybernetics  | 1995 | Wisdom Publications | **monograph** | low | title_corroborated | default:no_signals |
| 762 | Radical Constructivism: A Way of Knowing and  | 1995 | Falmer Press | **monograph** | low | curated_keyword | default:no_signals |
| 1261 | Social Systems | 1995 | Stanford University  | **monograph** | low | curated_keyword | default:no_signals |
| 1662 | A Recursive Vision: Ecological Understanding  | 1995 | University of Toront | **monograph** | low | curated_pure | default:no_signals |
| 274 | Neural Networks as Cybernetic Systems | 1996 | G. Thieme Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 753 | Cyberspace/Cyberbodies/Cyberpunk: Cultures of | 1996 | SAGE | **monograph** | low | curated_pure | default:no_signals |
| 1799 | Systemic Therapy With Individuals | 1996 | Karnac Books | **monograph** | low | curated_pure | default:no_signals |
| 233 | Technobrat: Culture in a Cybernetic Classroom | 1997 | HarperCollins Publ.  | **monograph** | low | title_only | default:no_signals |
| 1200 | Without Miracles: Universal Selection Theory  | 1997 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 279 | Making Sense of Behavior: The Meaning of Cont | 1998 | Benchmark Publicatio | **monograph** | low | curated_pure | default:no_signals |
| 1837 | Volleyball Cybernetics | 1998 | "Yes, I can!" Public | **monograph** | low | title_only | default:no_signals |
| 291 | How We Became Posthuman: Virtual Bodies in Cy | 1999 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 1299 | Fordern statt verwöhnen: die Erkenntnisse der | 1999 | Piper | **monograph** | low | curated_pure | default:no_signals |
| 1666 | Management Systems: A Viable Systems Approach | 1999 | Financial Times Mana | **monograph** | low | curated_pure | default:no_signals |
| 1667 | How Brains Make Up Their Minds | 1999 | Weidenfeld & Nicolso | **monograph** | low | curated_pure | default:no_signals |
| 198 | The Things We Do: Using the Lessons of Bernar | 2000 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 254 | Quantum Cybernetics: Toward a Unification of  | 2000 | Springer | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 1253 | The Reality of the Mass Media | 2000 | Stanford University  | **monograph** | low | curated_keyword | default:no_signals |
| 1255 | Art as a Social System | 2000 | Stanford University  | **monograph** | low | curated_keyword | default:no_signals |
| 1390 | Gaia: A New Look at Life on Earth | 2000 | OUP Oxford | **monograph** | low | curated_pure | default:no_signals |
| 1887 | The Mechanization of the Mind: On the Origins | 2000 | Princeton University | **monograph** | low | curated_keyword | default:no_signals |
| 240 | Sociocybernetics: Complexity, Autopoiesis, an | 2001 | Bloomsbury Publishin | **monograph** | low | curated_pure | default:no_signals |
| 445 | The Dream of Reality: Heinz Von Foerster’s Co | 2001 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 754 | The Modern Invention of Information: Discours | 2001 | SIU Press | **monograph** | low | curated_pure | default:no_signals |
| 1202 | On the Self-Regulation of Behavior | 2001 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 1996 | Living Systems: Theory and Application | 2001 | Nova Science Publish | **monograph** | low | curated_pure | default:no_signals |
| 180 | The PSYCHOCYBERNETIC MODEL OF ART THERAPY: (2 | 2002 | Charles C Thomas Pub | **monograph** | low | curated_keyword | default:no_signals |
| 186 | Marine Control Systems: Guidance, Navigation  | 2002 | Marine Cybernetics | **monograph** | low | curated_keyword | default:no_signals |
| 372 | Between Human and Machine: Feedback, Control, | 2002 | JHU Press | **monograph** | low | title_corroborated | default:no_signals |
| 436 | From Energy to Information: Representation in | 2002 | Stanford University  | **monograph** | low | curated_pure | default:no_signals |
| 442 | The Cybernetic Theory of Decision: New Dimens | 2002 | Princeton University | **monograph** | low | title_corroborated | default:no_signals |
| 1033 | Radical Constructivism in Action: Building on | 2002 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1192 | More Mind Readings: Methods and Models in the | 2002 | New View Publication | **monograph** | low | curated_pure | default:no_signals |
| 1701 | Control Theory for Humans: Quantitative Appro | 2002 | Taylor & Francis | **monograph** | low | curated_pure | default:no_signals |
| 1789 | Theories of Distinction: Redescribing the Des | 2002 | Stanford University  | **monograph** | low | curated_pure | default:no_signals |
| 126 | Narrative Gravity: Conversation, Cognition, C | 2003 | Routledge | **monograph** | low | metadata_search | default:no_signals |
| 247 | Rethinking Homeostasis: Allostatic Regulation | 2003 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 357 | Control and Modeling of Complex Systems: Cybe | 2003 | Birkhäuser | **monograph** | low | title_corroborated | default:no_signals |
| 771 | The Evolutionary Trajectory: The Growth of In | 2003 | CRC Press | **monograph** | low | curated_keyword | default:no_signals |
| 1127 | Self-Organization in Biological Systems | 2003 | Princeton University | **monograph** | low | curated_pure | default:no_signals |
| 1300 | Nature's Magic: Synergy in Evolution and the  | 2003 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 1743 | Telematic Embrace: Visionary Theories of Art, | 2003 | University of Califo | **monograph** | low | curated_keyword | default:no_signals |
| 1793 | Autopoietic Organization Theory: Drawing on N | 2003 | Abstrakt forlag | **monograph** | low | curated_pure | default:no_signals |
| 1794 | Natural-Born Cyborgs: Minds, Technologies, an | 2003 | Oxford University Pr | **monograph** | low | metadata_search | default:no_signals |
| 1841 | Communication and Cyberspace: Social Interact | 2003 | Hampton Press | **monograph** | low | curated_keyword | default:no_signals |
| 2000 | Understanding Systems: Conversations on Epist | 2003 | Springer US | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 195 | Tribute to Stafford Beer | 2004 | Emerald Group Publis | **monograph** | low | curated_keyword | default:no_signals |
| 280 | Machines Who Think: A Personal Inquiry Into t | 2004 | Taylor & Francis | **monograph** | low | curated_pure | default:no_signals |
| 416 | From Being to Doing: The Origins of the Biolo | 2004 | Carl-Auer Verlag | **monograph** | low | curated_pure | default:no_signals |
| 747 | Developing Second Order Cybernetics | 2004 | Emerald Group Publis | **monograph** | low | title_corroborated | default:no_signals |
| 1125 | Creativity as an Exact Science | 2004 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 1791 | Law as a Social System | 2004 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 1852 | March of the Machines: The Breakthrough in Ar | 2004 | University of Illino | **monograph** | low | curated_keyword | default:no_signals |
| 173 | World Weavers: Globalization, Science Fiction | 2005 | Hong Kong University | **monograph** | low | title_corroborated | default:no_signals |
| 202 | The Semantic Turn: A New Foundation for Desig | 2005 | Taylor & Francis | **monograph** | low | curated_pure | default:no_signals |
| 270 | On Purposeful Systems: An Interdisciplinary A | 2005 | Aldine Transaction | **monograph** | low | curated_pure | default:no_signals |
| 294 | Holistic Darwinism: Synergy, Cybernetics, and | 2005 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 373 | Behavior: The Control of Perception | 2005 | Benchmark Publicatio | **monograph** | low | curated_pure | default:no_signals |
| 750 | Heinz von Foerster - in memoriam | 2005 | Emerald Publishing | **monograph** | low | curated_pure | default:no_signals |
| 756 | Cultures of Control | 2005 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1258 | Risk: A Sociological Theory | 2005 | Aldine Transaction | **monograph** | low | curated_pure | default:no_signals |
| 1867 | Understanding Me: Lectures and Interviews | 2005 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 305 | From Counterculture to Cyberculture: Stewart  | 2006 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 336 | Cybernetics and Public Administration | 2006 | Emerald Publishing | **monograph** | low | title_only | default:no_signals |
| 427 | Collective Beings | 2006 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer, primo:type_other, primo:type_book→monograph |
| 767 | Festschrift for Felix Geyer | 2006 | Emerald Publishing | **monograph** | low | curated_pure | default:no_signals |
| 1385 | Self-Organization and Emergence in Life Scien | 2006 | Springer | **monograph** | medium | metadata_search | publisher:springer, primo:no_record |
| 1788 | Luhmann Explained: From Souls to Systems | 2006 | Open Court Publishin | **monograph** | low | curated_keyword | default:no_signals |
| 1893 | Digital Shock: Confronting the New Reality | 2006 |  | **monograph** | low | curated_keyword | default:no_signals |
| 340 | Cybernetics and Design | 2007 | Emerald Group Publis | **monograph** | low | title_only | default:no_signals |
| 382 | Architectural Principles in the Age of Cybern | 2007 | Routledge | **monograph** | low | title_only | default:no_signals |
| 385 | Anticipatory Behavior in ALS: From Brains to  | 2007 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:type_web_resource, openlibrary:proceedings_subject |
| 413 | Neocybernetics in Biological Systems | 2007 | Helsinki University  | **monograph** | low | curated_pure | default:no_signals |
| 433 | Biological Cybernetics Research Trends | 2007 | Nova Publishers | **monograph** | low | title_corroborated | default:no_signals |
| 766 | Beginning of a New Epistemology - In Memoriam | 2007 | Emerald Publishing | **monograph** | low | curated_pure | default:no_signals |
| 1035 | Key Works in Radical Constructivism | 2007 | Sense Publishers | **monograph** | low | curated_pure | default:no_signals |
| 1036 | Wie wir uns erfinden: eine Autobiographie des | 2007 | Carl-Auer-Verlag | **monograph** | low | curated_pure | default:no_signals |
| 1082 | Imaginary Futures: From Thinking Machines to  | 2007 | Pluto Press | **monograph** | low | curated_pure | default:no_signals |
| 1178 | Cybernetical Physics: From Control of Chaos t | 2007 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1204 | Systems Biology: Philosophical Foundations | 2007 | Elsevier | **monograph** | low | curated_pure | default:no_signals |
| 1695 | Casting Nets and Testing Specimens: Two Grand | 2007 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1780 | Composing a Life | 2007 | Grove Press | **monograph** | low | curated_pure | default:no_signals |
| 231 | The Allure of Machinic Life: Cybernetics, Art | 2008 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 269 | On Communicating: Otherness, Meaning, and Inf | 2008 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 323 | Cybersemiotics: Why Information Is Not Enough | 2008 | University of Toront | **monograph** | low | curated_keyword | default:no_signals |
| 361 | Constructing Soviet Cultural Policy: Cybernet | 2008 | Tema Q (Culture Stud | **monograph** | low | title_only | default:no_signals |
| 391 | A Legacy for Living Systems: Gregory Bateson  | 2008 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 903 | Reviving the Living: Meaning Making in Living | 2008 | Elsevier Science | **monograph** | low | curated_pure | default:no_signals |
| 1402 | Systems Research for Behavioral Science: A So | 2008 | Transaction Publishe | **monograph** | low | curated_keyword | default:no_signals |
| 1663 | The Mechanical Mind in History | 2008 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1775 | Living Control Systems III: The Fact of Contr | 2008 |  | **monograph** | low | curated_pure | default:no_signals |
| 1785 | Communication: The Social Matrix of Psychiatr | 2008 | Transaction Publishe | **monograph** | low | curated_pure | default:no_signals |
| 219 | The Digital Cast of Being: Metaphysics, Mathe | 2009 | Ontos-Verlag | **monograph** | low | title_only | default:no_signals |
| 313 | Emotional Intelligence: A Cybernetic Approach | 2009 | Springer | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 388 | A Missing Link in Cybernetics | 2009 | Springer | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 456 | Sociology and Complexity Science: A New Field | 2009 | Springer | **monograph** | medium | metadata_search | publisher:springer, primo:no_record |
| 671 | Think Before You Think: Social Complexity and | 2009 | Wavestone Press | **monograph** | low | curated_keyword | default:no_signals |
| 1210 | Cyburbia : The Dangerous Idea That's Changing | 2009 | Little Brown | **monograph** | low | curated_pure | default:no_signals |
| 1741 | Digital Culture | 2009 | Reaktion Books | **monograph** | low | curated_pure | default:no_signals |
| 1744 | The Scientific Way of Warfare: Order and Chao | 2009 | Columbia University  | **monograph** | low | curated_keyword | default:no_signals |
| 221 | The Discovery of the Artificial: Behavior, Mi | 2010 | Springer Netherlands | **monograph** | medium | title_only | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 394 | Ahead of Change: How Crowd Psychology and Cyb | 2010 | Campus Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 397 | A Foray Into the Worlds of Animals and Humans | 2010 | Univ Of Minnesota Pr | **monograph** | low | curated_pure | default:no_signals |
| 1194 | Dialogue Concerning the Two Chief Approaches  | 2010 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1226 | Project: Soul Catcher: Secrets of Cyber and C | 2010 | CreateSpace Independ | **monograph** | low | title_corroborated | default:no_signals |
| 1384 | Cyberfiction: After the Future | 2010 | Palgrave Macmillan | **monograph** | low | curated_keyword | default:no_signals |
| 1391 | Gaia in Turmoil: Climate Change, Biodepletion | 2010 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1748 | Organizations: Social Systems Conducting Expe | 2010 | Springer Berlin Heid | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 1917 | Cyborgs in Latin America | 2010 | Palgrave Macmillan U | **monograph** | low | curated_pure | default:no_signals |
| 230 | The Cybernetic Brain: Sketches of Another Fut | 2011 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 263 | Perspectives on Information | 2011 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 265 | Organizational Systems: Managing Complexity W | 2011 | Springer Berlin Heid | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 359 | Context and Complexity: Cultivating Contextua | 2011 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 398 | A Cybernetic View of Biological Growth: The M | 2011 | Cambridge University | **monograph** | low | title_corroborated | default:no_signals |
| 1118 | Relative Information: Theories and Applicatio | 2011 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1418 | Computation in Cells and Tissues: Perspective | 2011 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1461 | Cybernetic Revolutionaries: Technology and Po | 2011 | The MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 1503 | The Creation of Reality: A Constructivist Epi | 2011 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1697 | The Dilemma of Enquiry and Learning | 2011 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1850 | This Is Not a Program | 2011 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 266 | Organization Structure: Cybernetic Systems Fo | 2012 | Springer Science & B | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 289 | Information and Reflection: On Some Problems  | 2012 | Springer Science & B | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 344 | Cybernetic Revelation: Deconstructing Artific | 2012 | Post Egoism Media | **monograph** | low | title_corroborated | default:no_signals |
| 383 | Anticipatory Systems: Philosophical, Mathemat | 2012 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 404 | The Origin of Humanness in the Biology of Lov | 2012 | Andrews UK Limited | **monograph** | low | curated_pure | default:no_signals |
| 424 | The Application of Cybernetic Analysis to the | 2012 | Springer | **monograph** | medium | title_only | publisher:springer, primo:type_web_resource |
| 574 | Positive Feedback in Natural Systems | 2012 | Springer Berlin Heid | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 746 | Information Theory and Evolution | 2012 | World Scientific | **monograph** | low | metadata_search | default:no_signals |
| 1126 | Design and Diagnosis for Sustainable Organiza | 2012 | Springer Science & B | **monograph** | medium | curated_keyword | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1228 | Futures We Are In | 2012 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer, primo:type_web_resource |
| 1229 | A Choice of Futures | 2012 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer, primo:type_web_resource |
| 1694 | Ways of Learning and Knowing: The Epistemolog | 2012 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1699 | Control in the Classroom: An Adventure in Lea | 2012 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1765 | Autopoiesis and Configuration Theory: New App | 2012 | Springer Netherlands | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 116 | Systems Methodology for the Management Scienc | 2013 | Springer US | **monograph** | medium | metadata_search | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 196 | Traditions of Systems Theory: Major Figures a | 2013 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 255 | Processes and Boundaries of the Mind: Extendi | 2013 | Springer Science & B | **monograph** | medium | curated_pure | publisher:springer, primo:type_web_resource |
| 262 | Polish Cybernetic Poetry | 2013 |  | **monograph** | low | title_only | default:no_signals |
| 282 | Knowledge and Systems Science: Enabling Syste | 2013 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 348 | Cybernetic Approach to Project Management | 2013 | Springer | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 350 | Culture Contact in Evenki Land: A Cybernetic  | 2013 | Global Oriental | **monograph** | low | title_corroborated | default:no_signals |
| 407 | The Certainty of Uncertainty: Dialogues Intro | 2013 | Andrews UK Limited | **monograph** | low | curated_keyword | default:no_signals |
| 441 | The Cybernetic Society: Pergamon Unified Engi | 2013 | Elsevier | **monograph** | low | title_corroborated | default:no_signals |
| 907 | Beiträge zur Grundlegung einer operationsfähi | 2013 | Meiner, F | **monograph** | low | title_only | default:no_signals |
| 1022 | Summa Technologiae | 2013 | U of Minnesota Press | **monograph** | low | curated_pure | default:no_signals |
| 1563 | Self-Producing Systems: Implications and Appl | 2013 | Springer US | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1698 | The Death of Jeffrey Stapleton: Exploring the | 2013 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1972 | Probability Theory, Mathematical Statistics,  | 2013 | Springer Science & B | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 182 | The Beginning of Heaven and Earth Has No Name | 2014 | Fordham University P | **monograph** | low | title_corroborated | default:no_signals |
| 249 | Reflexion and Control: Mathematical Models | 2014 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 278 | Neocybernetics and Narrative | 2014 | U of Minnesota Press | **monograph** | low | curated_pure | default:no_signals |
| 288 | Innovative Approaches Towards Low Carbon Econ | 2014 | Springer Berlin Heid | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 334 | Cybernetics and the Philosophy of Mind | 2014 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 409 | Rhetoric and Ethics in the Cybernetic Age: Th | 2014 | Routledge | **monograph** | low | title_only | default:no_signals |
| 425 | The Magic Ring: Systems Thinking Approach to  | 2014 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 772 | Biomolecular Feedback Systems | 2014 | Princeton University | **monograph** | low | curated_pure | default:no_signals |
| 916 | La Cybernétique | 2014 | Editions du Seuil | **monograph** | low | curated_keyword | default:no_signals |
| 1040 | The Unleashed Scandal: The End of Control in  | 2014 | Andrews UK Limited | **monograph** | low | curated_pure | default:no_signals |
| 1086 | Indexing It All: The Subject in the Age of Do | 2014 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1220 | Virtually Human: The Promise—and the Peril—of | 2014 | St. Martin's Press | **monograph** | low | curated_pure | default:no_signals |
| 1531 | From Cells to Societies: Models of Complex Co | 2014 | Springer Berlin Heid | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1777 | Ontology of Complexity: A Reading of Gregory  | 2014 | CreateSpace Independ | **monograph** | low | curated_keyword | default:no_signals |
| 222 | The Cybernetics Moment: Or Why We Call Our Ag | 2015 | JHU Press | **monograph** | low | title_corroborated | default:no_signals |
| 301 | General System Theory: Foundations, Developme | 2015 | George Braziller Inc | **monograph** | low | curated_pure | default:no_signals |
| 315 | Systems | 2015 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 332 | Cybernetics: From Past to Future | 2015 | Springer | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 358 | Control: Digitality as Cultural Logic | 2015 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 365 | Cognitive Systems | 2015 |  | **monograph** | low | curated_keyword | default:no_signals |
| 406 | The Internet Revolution: From Dot-Com Capital | 2015 | Institute of Network | **monograph** | low | title_corroborated | default:no_signals |
| 414 | @Heaven: The Online Death of a Cybernetic Fut | 2015 | OR Books | **monograph** | low | title_only | default:no_signals |
| 911 | Entwicklungspsychopathologie und Psychotherap | 2015 | Springer Fachmedien  | **monograph** | medium | curated_pure | publisher:springer, primo:no_record, google:short_47pp |
| 914 | Exploring Cybernetics: Kybernetik im interdis | 2015 | Springer Fachmedien  | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 1443 | Anticipation: Learning From the Past: The Rus | 2015 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record, google:anthology_subtitle |
| 1523 | Jakob Von Uexküll: The Discovery of the Umwel | 2015 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1626 | Cyber-Proletariat: Global Labour in the Digit | 2015 | Pluto Press | **monograph** | low | curated_pure | default:no_signals |
| 1659 | Earth, Life, and System: Evolution and Ecolog | 2015 | Fordham University P | **monograph** | low | curated_pure | default:no_signals |
| 1766 | Karl W. Deutsch: Pioneer in the Theory of Int | 2015 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 194 | Architecture and Adaptation: From Cybernetics | 2016 | Routledge, Taylor &  | **monograph** | low | title_only | default:no_signals |
| 204 | The Question Concerning Technology in China:  | 2016 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 238 | Strategy for Managing Complex Systems: A Cont | 2016 | Campus Verlag | **monograph** | low | title_corroborated | default:no_signals |
| 252 | Rebel Genius: Warren S. McCulloch's Transdisc | 2016 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 268 | On the Existence of Digital Objects | 2016 | University of Minnes | **monograph** | low | curated_pure | default:no_signals |
| 326 | Cybernetics: The Macy Conferences 1946-1953 : | 2016 | University of Chicag | **monograph** | low | title_corroborated | default:no_signals |
| 338 | Cybernetics and Development: International Se | 2016 | Elsevier | **monograph** | low | title_corroborated | default:no_signals |
| 908 | Cybernetic Government: Informationstechnologi | 2016 | Springer Fachmedien  | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 913 | L'Empire cybernétique. Des machines à penser  | 2016 | Editions du Seuil | **monograph** | low | curated_pure | default:no_signals |
| 1116 | Anticipation and Medicine | 2016 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1193 | Hold That Thought: Two Steps to Effective Cou | 2016 | New View Publication | **monograph** | low | curated_pure | default:no_signals |
| 1201 | Perceptual Control Theory: An Overview of the | 2016 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1232 | The Power of Systems: How Policy Sciences Ope | 2016 | Cornell University P | **monograph** | low | curated_keyword | default:no_signals |
| 1524 | Cultural Implications of Biosemiotics | 2016 | Springer Netherlands | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1528 | Small Arcs of Larger Circles: Framing Through | 2016 | Triarchy Press | **monograph** | low | curated_pure | default:no_signals |
| 1732 | Machine Art in the Twentieth Century | 2016 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1733 | New Tendencies: Art at the Threshold of the I | 2016 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1909 | Machines of Loving Grace: The Quest for Commo | 2016 | HarperCollins | **monograph** | low | curated_pure | default:no_signals |
| 171 | Applied Systems Theory | 2017 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 210 | The Nature of the Machine and the Collapse of | 2017 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 217 | The Embodied Mind, Revised Edition: Cognitive | 2017 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 327 | Cybernetics, Warfare and Discourse: The Cyber | 2017 | Springer Internation | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 369 | Cinema, Trance and Cybernetics | 2017 | Amsterdam University | **monograph** | low | title_corroborated | default:no_signals |
| 412 | New Horizons for Second-Order Cybernetics | 2017 | World Scientific | **monograph** | low | title_corroborated | default:no_signals |
| 758 | Confronting the Machine: An Enquiry Into the  | 2017 | De Gruyter | **monograph** | low | curated_pure | default:no_signals |
| 1044 | Intangible Life: Functorial Connections in Re | 2017 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1085 | How the Mind Comes Into Being | 2017 | Oxford University Pr | **monograph** | low | metadata_search | default:no_signals |
| 1089 | Unthought: The Power of the Cognitive Noncons | 2017 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 1112 | A Complexity Approach to Sustainability: Theo | 2017 | World Scientific | **monograph** | low | curated_pure | default:no_signals |
| 1246 | Trust and Power | 2017 | Polity | **monograph** | low | curated_pure | default:no_signals |
| 1504 | Border Security: Shores of Politics, Horizons | 2017 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 1756 | Application of New Cybernetics in Physics | 2017 | Elsevier Science | **monograph** | low | title_corroborated | default:no_signals |
| 174 | What Is Information? | 2018 | University of Minnes | **monograph** | low | curated_pure | default:no_signals |
| 192 | Cybernetic Modeling for Bioreaction Engineeri | 2018 | Cambridge University | **monograph** | low | title_corroborated | default:no_signals |
| 276 | Neural Network Modeling: Statistical Mechanic | 2018 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 306 | Flatline Constructs: Gothic Materialism and C | 2018 | Exmilitary | **monograph** | low | title_corroborated | default:no_signals |
| 403 | The Soft Machine: Cybernetic Fiction | 2018 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 405 | The Opening of the Cybernetic Frontier: Citie | 2018 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 419 | Cybernetics and Applied Systems | 2018 | CRC Press | **monograph** | low | title_corroborated | default:no_signals |
| 426 | From Collective Beings to Quasi-Systems | 2018 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 597 | Between an Animal and a Machine: Stanislaw Le | 2018 | Peter Lang | **monograph** | low | curated_keyword | default:no_signals |
| 761 | Routledge Library Editions: Artificial Intell | 2018 | Taylor & Francis Gro | **monograph** | low | metadata_search | default:no_signals |
| 1042 | What Does It Mean to Be Human? Life, Death, P | 2018 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1081 | Worldmaking as Techné: Participatory Art, Mus | 2018 | Riverside Architectu | **monograph** | low | curated_pure | default:no_signals |
| 1088 | Socially Extended Epistemology | 2018 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 1230 | Energy, Information, Feedback, Adaptation, an | 2018 | Springer | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 1234 | The Dream Machine | 2018 | Stripe Press | **monograph** | low | curated_pure | default:no_signals |
| 1238 | Artificial Intelligence: Its Philosophy and N | 2018 | Routledge, Taylor &  | **monograph** | low | curated_pure | default:no_signals |
| 1257 | Organization and Decision | 2018 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 1383 | French Philosophy of Technology: Classical Re | 2018 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 1387 | Film in the Anthropocene: Philosophy, Ecology | 2018 | Palgrave Macmillan | **monograph** | low | title_corroborated | default:no_signals |
| 1393 | Gods and Robots: Myths, Machines, and Ancient | 2018 | Princeton University | **monograph** | low | curated_pure | default:no_signals |
| 1661 | An Epistemology of Noise | 2018 | Bloomsbury Publishin | **monograph** | low | curated_pure | default:no_signals |
| 1890 | Complexity Sciences: Theoretical and Empirica | 2018 | Cambridge Scholars P | **monograph** | low | curated_pure | default:no_signals |
| 175 | What Is Health? Allostasis and the Evolution  | 2019 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 206 | Thermodynamics and Regulation of Biological P | 2019 | Walter de Gruyter Gm | **monograph** | low | curated_keyword | default:no_signals |
| 248 | Recursivity and Contingency | 2019 | Bloomsbury Academic | **monograph** | low | curated_keyword | default:no_signals |
| 341 | Cybernetics or Control and Communication in t | 2019 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 345 | Cybernetic frameworks for a shared world | 2019 | Springer | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 381 | Art, Cybernetics and Pedagogy in Post-War Bri | 2019 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 399 | A Cybernetic Approach to the Assessment of Ch | 2019 | Taylor & Francis Gro | **monograph** | low | title_corroborated | default:no_signals |
| 417 | Design Cybernetics: Navigating the New | 2019 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 748 | Rethinking Higher Education for the 21st Cent | 2019 | Emerald Publishing | **monograph** | low | curated_keyword | default:no_signals |
| 751 | Communication as Gesture: Media(tion), Meanin | 2019 | Emerald Group Publis | **monograph** | low | curated_keyword | default:no_signals |
| 757 | Systems Theories for Psychotherapists: From T | 2019 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1043 | Jim Dator: A Noticer in Time: Selected Work,  | 2019 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1084 | Documentarity: Evidence, Ontology, and Inscri | 2019 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1128 | The Culture of Feedback: Ecological Thinking  | 2019 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 1291 | The Self-organizing Polity: An Epistemologica | 2019 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 1293 | The Creative Therapist in Practice | 2019 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 1348 | Management Control Theory | 2019 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1499 | Thinking Race: Social Myths and Biological Re | 2019 | Rowman & Littlefield | **monograph** | low | curated_pure | default:no_signals |
| 1740 | The Meaning of Information | 2019 | Walter de Gruyter Gm | **monograph** | low | curated_pure | default:no_signals |
| 1783 | Philosophical Posthumanism | 2019 | Bloomsbury Academic | **monograph** | low | curated_pure | default:no_signals |
| 1955 | No More Feedback: Cultivate Consciousness at  | 2019 | InterOctave | **monograph** | low | curated_pure | default:no_signals |
| 1957 | The Beauty of Detours: A Batesonian Philosoph | 2019 | SUNY Press | **monograph** | low | curated_pure | default:no_signals |
| 224 | The Cybernetic Hypothesis | 2020 | MIT Press | **monograph** | low | title_corroborated | default:no_signals |
| 302 | Gaian Systems: Lynn Margulis, Neocybernetics, | 2020 | University of Minnes | **monograph** | low | curated_keyword | default:no_signals |
| 316 | Discourses in Action: What Language Enables U | 2020 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 377 | Automated Media | 2020 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 387 | Anarchist Cybernetics: Control and Communicat | 2020 | Policy Press | **monograph** | low | title_corroborated | default:no_signals |
| 401 | Cybernetic-Existentialism: Freedom, Systems,  | 2020 | Taylor & Francis Gro | **monograph** | low | title_corroborated | default:no_signals |
| 420 | Cybernetic Psychology and Mental Health: A Ci | 2020 | Routledge, Taylor &  | **monograph** | low | title_corroborated | default:no_signals |
| 667 | Gregory Bateson on Relational Communication:  | 2020 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 755 | Sociocybernetics and Political Theory in a Co | 2020 | BRILL | **monograph** | low | curated_keyword | default:no_signals |
| 764 | Systems Thinking for a Turbulent World: A Sea | 2020 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1124 | Resilience in the Anthropocene: Governance an | 2020 | Taylor & Francis Gro | **monograph** | low | curated_pure | default:no_signals |
| 1231 | Data Loam: Sometimes Hard, Usually Soft. The  | 2020 | Walter de Gruyter Gm | **monograph** | low | curated_pure | default:no_signals |
| 1245 | The Hidden Power of Systems Thinking: Governa | 2020 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 1292 | Jakob Von Uexküll and Philosophy: Life, Envir | 2020 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 1430 | For the Love of Cybernetics: Personal Narrati | 2020 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 1589 | Think Tank Aesthetics: Midcentury Modernism,  | 2020 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1745 | Utopics: The Unification of Human Science | 2020 | Springer Internation | **monograph** | medium | curated_keyword | publisher:springer, primo:no_record |
| 1921 | Machine Sensation: Anthropomorphism and 'Natu | 2020 | Open Humanities Pres | **monograph** | low | curated_keyword | default:no_signals |
| 1952 | Understanding the Knowledge Society: A New Pa | 2020 | Edward Elgar Publish | **monograph** | low | curated_pure | default:no_signals |
| 1953 | The American Robot: A Cultural History | 2020 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 1954 | The Systemic Approach in Sociology and Niklas | 2020 | Emerald Publishing L | **monograph** | low | curated_pure | default:no_signals |
| 200 | The Study of Living Control Systems: A Guide  | 2021 | Cambridge University | **monograph** | low | curated_pure | default:no_signals |
| 201 | Thinking by Machine: A Study of Cybernetics / | 2021 | Creative Media Partn | **monograph** | low | title_only | default:no_signals |
| 220 | The Digitally Disposed: Racial Capitalism and | 2021 | University of Minnes | **monograph** | low | curated_keyword | default:no_signals |
| 251 | Recent Advances in Soft Computing and Cyberne | 2021 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 292 | Human 4.0: From Biology to Cybernetic | 2021 | BoD – Books on Deman | **monograph** | low | title_only | default:no_signals |
| 322 | Deconstructing Health Inequity: A Perceptual  | 2021 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 333 | Cybernetics for the Social Sciences | 2021 | BRILL | **monograph** | low | title_corroborated | default:no_signals |
| 363 | Concerning Stephen Willats and the Social Fun | 2021 | Bloomsbury Publishin | **monograph** | low | title_corroborated | default:no_signals |
| 765 | Narratives of Scale in the Anthropocene: Imag | 2021 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1020 | Dialogues | 2021 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1205 | Life Out of Balance: Homeostasis and Adaptati | 2021 | University Alabama P | **monograph** | low | curated_keyword | default:no_signals |
| 1225 | Adolescent Risk Behavior and Self-Regulation: | 2021 | Springer Nature | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 1269 | Cybernetics Without Mathematics | 2021 | Hassell Street Press | **monograph** | low | title_only | default:no_signals |
| 1304 | When Brains Meet Buildings | 2021 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 1377 | Agricultural Cybernetics | 2021 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 1665 | A Configuration Approach to Mindset Agency Th | 2021 | Cambridge University | **monograph** | low | curated_keyword | default:no_signals |
| 1735 | Artificial Intelligence, Interaction, Perform | 2021 | Independently Publis | **monograph** | low | curated_pure | default:no_signals |
| 2010 | Embodiment of the Everyday Cyborg: Technologi | 2021 | Manchester Universit | **monograph** | low | curated_keyword | default:no_signals |
| 209 | The New Technological Condition: Architecture | 2022 | Birkhäuser | **monograph** | low | title_corroborated | default:no_signals |
| 237 | World Organization of Systems and Cybernetics | 2022 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 310 | Ethical and Aesthetic Explorations of Systemi | 2022 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 318 | Designing and Managing Complex Systems | 2022 | Elsevier Science | **monograph** | low | curated_pure | default:no_signals |
| 342 | Cybernetics 2.0: A General Theory of Adaptivi | 2022 | Springer | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 366 | Complex Systems: Spanning Control and Computa | 2022 | Springer Internation | **monograph** | medium | title_only | publisher:springer, primo:no_record |
| 421 | Cybernetic Architectures: Informational Think | 2022 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 760 | Sustainable Self-Governance in Businesses and | 2022 | Routledge | **monograph** | low | curated_keyword | default:no_signals |
| 1049 | Beyond Identities: Human Becomings in Weirdin | 2022 | Springer | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1117 | Epigenetics and Anticipation | 2022 | Springer Nature | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1132 | The Neurology of Business: Implementing the V | 2022 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1133 | Semiotic Agency: Science Beyond Mechanism | 2022 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1134 | Hormones and Reality: Epigenetic Regulation o | 2022 | Springer Internation | **monograph** | medium | curated_pure | publisher:springer, primo:no_record |
| 1252 | The Making of Meaning: From the Individual to | 2022 | Oxford University Pr | **monograph** | low | curated_pure | default:no_signals |
| 1276 | Northern Sparks: Innovation, Technology Polic | 2022 | MIT Press | **monograph** | low | curated_keyword | default:no_signals |
| 1386 | Complex System Governance: Theory and Practic | 2022 | Springer Internation | **monograph** | medium | metadata_search | publisher:springer, primo:no_record |
| 1419 | Digital Fever: Taming the Big Business of Dis | 2022 | Palgrave Macmillan | **monograph** | low | curated_pure | default:no_signals |
| 1435 | Artificial Intelligence in Accounting | 2022 | Routledge | **monograph** | low | metadata_search | default:no_signals |
| 1456 | The Informational Logic of Human Rights: Netw | 2022 | Edinburgh University | **monograph** | low | title_only | default:no_signals |
| 1457 | Order in Chaos - Cybernetics of Brand Managem | 2022 | Springer Berlin Heid | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record, google:short_47pp |
| 1738 | Climatic Media: Transpacific Experiments in A | 2022 | Duke University Pres | **monograph** | low | curated_keyword | default:no_signals |
| 1757 | Architecture in Digital Culture: Machines, Ne | 2022 | Routledge/Taylor & F | **monograph** | low | curated_pure | default:no_signals |
| 1758 | Brainmedia: One Hundred Years of Performing L | 2022 | Bloomsbury Academic | **monograph** | low | curated_pure | default:no_signals |
| 1762 | Last Futures: Nature, Technology and the End  | 2022 | Verso Books | **monograph** | low | curated_pure | default:no_signals |
| 1763 | Twins and Recursion in Digital, Literary and  | 2022 | Bloomsbury Academic | **monograph** | low | curated_keyword | default:no_signals |
| 1764 | Nervous Systems: Art, Systems, and Politics S | 2022 | Duke University Pres | **monograph** | low | curated_pure | default:no_signals |
| 1922 | The Dark Posthuman: Dehumanization, Technolog | 2022 | punctum books | **monograph** | low | curated_keyword | default:no_signals |
| 105 | The Experience Machine: How Our Minds Predict | 2023 | Pantheon | **monograph** | low | curated_pure | default:no_signals |
| 347 | Cybernetic Aesthetics: Modernist Networks of  | 2023 | Cambridge University | **monograph** | low | title_corroborated | default:no_signals |
| 368 | Code: From Information Theory to French Theor | 2023 | Duke University Pres | **monograph** | low | curated_keyword | default:no_signals |
| 1272 | Balkan Cyberia: Cold War Computing, Bulgarian | 2023 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1277 | Art + DIY Electronics | 2023 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1278 | Evolution "On Purpose": Teleonomy in Living S | 2023 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1338 | Frictions: Inquiries Into Cybernetic Thinking | 2023 | meson Press eG | **monograph** | low | title_corroborated | default:no_signals |
| 1508 | Unstable Nature: Order, Entropy, Becoming | 2023 | CRC Press | **monograph** | low | curated_pure | default:no_signals |
| 1706 | Health as a Social System: Luhmann's Theory A | 2023 | transcript Verlag | **monograph** | low | curated_pure | default:no_signals |
| 1736 | With and Against: The Situationist Internatio | 2023 | Verso Books | **monograph** | low | curated_keyword | default:no_signals |
| 1737 | Art and Knowledge After 1900: Interactions Be | 2023 | Manchester Universit | **monograph** | low | curated_keyword | default:no_signals |
| 1759 | Organism-Oriented Ontology | 2023 | Edinburgh University | **monograph** | low | curated_pure | default:no_signals |
| 1782 | Laws of Form: A Fiftieth Anniversary | 2023 | World Scientific | **monograph** | low | curated_pure | default:no_signals |
| 1940 | Algorithms: Technology, Culture, Politics | 2023 | Routledge, Taylor &  | **monograph** | low | curated_pure | default:no_signals |
| 1945 | Experimenting the Human: Art, Music, and the  | 2023 | University of Chicag | **monograph** | low | curated_keyword | default:no_signals |
| 1946 | Interactive Design: Towards a Responsive Envi | 2023 | Walter de Gruyter Gm | **monograph** | low | curated_keyword | default:no_signals |
| 402 | Unconscious Intelligence in Cybernetic Psycho | 2024 | Routledge, Taylor &  | **monograph** | low | title_corroborated | default:no_signals |
| 1279 | The Brain Abstracted: Simplification in the H | 2024 | MIT Press | **monograph** | low | curated_pure | default:no_signals |
| 1352 | The Cybernetic Border: Drones, Technology, an | 2024 | Duke University Pres | **monograph** | low | title_corroborated | default:no_signals |
| 1452 | Cybernetics of Art: Reason and the Rainbow | 2024 | Routledge, Chapman & | **monograph** | low | title_corroborated | default:no_signals |
| 1454 | Cybernetics and the Constructed Environment:  | 2024 | Routledge | **monograph** | low | title_corroborated | default:no_signals |
| 1502 | Truth Is the Invention of a Liar: Conversatio | 2024 | Carl-Auer Verlag | **monograph** | low | curated_keyword | default:no_signals |
| 1558 | Cybernetic Avatar | 2024 | Springer Nature Sing | **monograph** | medium | title_corroborated | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1607 | Music, the Avant-Garde, and Counterculture: I | 2024 | Springer Nature Swit | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1625 | Machine and Sovereignty: For a Planetary Thin | 2024 | U of Minnesota Press | **monograph** | low | curated_pure | default:no_signals |
| 1633 | Christian Eschatology of Artificial Intellige | 2024 | Becoming Press | **monograph** | low | title_corroborated | default:no_signals |
| 1653 | Relational Improvisation: Music, Dance and Co | 2024 | Routledge, Taylor &  | **monograph** | low | curated_keyword | default:no_signals |
| 1696 | Powers of Perceptual Control, Volume I: An In | 2024 | Living Control Syste | **monograph** | low | curated_pure | default:no_signals |
| 1702 | Organic Modernism: From the British Bauhaus t | 2024 | Bloomsbury Academic | **monograph** | low | title_corroborated | default:no_signals |
| 1715 | Cybernetic Revolution and Global Aging: Human | 2024 | Springer Internation | **monograph** | medium | title_corroborated | publisher:springer, primo:no_record |
| 1751 | Theory and Practice of Decision Making in Reg | 2024 | Taylor & Francis Lim | **monograph** | low | curated_pure | default:no_signals |
| 1752 | From Systems to Actor-Networks: A Paradigm Sh | 2024 | Ethics International | **monograph** | low | curated_pure | default:no_signals |
| 1754 | The Riddle of Organismal Agency: New Historic | 2024 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1755 | Patterns: Theory of the Digital Society | 2024 | Polity Press | **monograph** | low | curated_pure | default:no_signals |
| 1914 | Bateson’s Alphabet: The ABC's of Gregory Bate | 2024 | University of Michig | **monograph** | low | curated_pure | default:no_signals |
| 1919 | The Politics and Ethics of Transhumanism: Tec | 2024 | Policy Press | **monograph** | low | curated_pure | default:no_signals |
| 1937 | Anime's Knowledge Cultures: Geek, Otaku, Zhai | 2024 | University of Minnes | **monograph** | low | curated_pure | default:no_signals |
| 1941 | Organization Studies and Posthumanism: Toward | 2024 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1942 | Cyberboss: The Rise of Algorithmic Management | 2024 | Verso Books | **monograph** | low | curated_pure | default:no_signals |
| 1551 | Cybernetic Capitalism: A Critical Theory of t | 2025 | Fordham Univ Press | **monograph** | low | title_corroborated | default:no_signals |
| 1622 | Cybernetic Circulation Complex: Big Tech and  | 2025 | Verso Books | **monograph** | low | title_corroborated | default:no_signals |
| 1746 | Utopia in the Factory: Prefigurative Knowledg | 2025 | Springer Nature Swit | **monograph** | medium | title_corroborated | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1760 | Unifying Systems: Information, Feedback, and  | 2025 | Springer Nature Swit | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1854 | Bacteria to AI: Human Futures With Our Nonhum | 2025 | University of Chicag | **monograph** | low | curated_pure | default:no_signals |
| 1915 | The Mathematical Theory of Semantic Communica | 2025 | Springer Nature Sing | **monograph** | medium | curated_pure | publisher:springer, primo:type_book→monograph, primo:type_book→monograph |
| 1916 | The Ethics of AI: Power, Critique, Responsibi | 2025 | Policy Press | **monograph** | low | curated_pure | default:no_signals |
| 1933 | Behaviourist Art and Cybernetics: Mapping a F | 2025 | Routledge, Chapman & | **monograph** | low | title_corroborated | default:no_signals |
| 1935 | Creative Work and Distributions of Power | 2025 | Routledge | **monograph** | low | curated_pure | default:no_signals |
| 1938 | Through the Screen: Towards a General Philoso | 2025 | De Gruyter | **monograph** | low | curated_keyword | default:no_signals |
| 1947 | Reading Talcott Parsons: A Re-Assessment of H | 2025 | Taylor & Francis Gro | **monograph** | low | curated_pure | default:no_signals |
| 1973 | Acting With the World: Agency in the Anthropo | 2025 | Duke University Pres | **monograph** | low | curated_pure | default:no_signals |
| 1986 | Concrete Encoded: Poetry, Design, and the Cyb | 2025 | University of Texas  | **monograph** | low | title_corroborated | default:no_signals |
| 2004 | The Composer's Black Box: Making Music in Cyb | 2025 | University of Califo | **monograph** | low | title_corroborated | default:no_signals |
| 1268 | Engineering Cybernetics | 1954 | McGraw-Hill | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:no_record |
| 375 | Cybernetics and Management | 1959 | Wiley | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:no_record |
| 1177 | An Introduction to Information Theory: Symbol | 1961 | Dover Publications | **textbook** | high | metadata_search | title:introduction_to, primo:type_book→monograph, primo:type_book→monograph |
| 1863 | Intelligent Machines: An Introduction to Cybe | 1962 | Blaisdell Publishing | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record, google:textbook_subtitle |
| 1828 | Man, Memory, and Machines: An Introduction to | 1964 | Macmillan | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record, google:textbook_subtitle |
| 1822 | Fundamentals of Engineering Cybernetics | 1965 | Israel Program for S | **textbook** | high | title_corroborated | title:fundamentals_of, primo:no_record |
| 1613 | Cybernetic Principles of Learning and Educati | 1966 | Holt, Rinehart and W | **textbook** | medium | title_only | title:principles_of, primo:no_record |
| 1634 | Decision and Control: The Meaning of Operatio | 1966 | Wiley | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:no_record |
| 1832 | Introduction to Cybernetics | 1966 | Academic Press | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record |
| 663 | Introduction to Medical Cybernetics: By v. V. | 1967 | National Aeronautics | **textbook** | high | title_only | title:introduction_to, primo:no_record |
| 1520 | Principles of Systems | 1968 | Pegasus Communicatio | **textbook** | medium | curated_pure | title:principles_of, primo:no_record |
| 283 | Introduction to Economic Cybernetics | 1970 | Elsevier | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record |
| 568 | The Metaphorical Brain: An Introduction to Cy | 1972 | Wiley-Interscience | **textbook** | high | title_corroborated | title:introduction_to, publisher:textbook_house, primo:type_book→monograph |
| 435 | Communication and Organizational Control: Cyb | 1974 | Wiley | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:no_record |
| 1823 | The Anatomy of Business: An Introduction to B | 1974 | Wiley | **textbook** | high | title_corroborated | title:introduction_to, publisher:textbook_house, primo:no_record |
| 1992 | The Anatomy of Business: An Introduction to B | 1974 | Associated Business  | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record, google:textbook_subtitle |
| 1851 | On the Texture of Brains: An Introduction to  | 1977 | Springer-Verlag | **textbook** | high | curated_keyword | title:introduction_to, publisher:springer, primo:no_record |
| 1119 | Living Systems | 1978 | McGraw-Hill | **textbook** | medium | curated_pure | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 1784 | The Rise of Systems Theory: An Ideological An | 1978 | Wiley | **textbook** | medium | curated_keyword | publisher:textbook_house, primo:no_record |
| 672 | The Heart of Enterprise | 1979 | Wiley | **textbook** | medium | curated_pure | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 1302 | Principles of Biological Autonomy | 1979 | North Holland | **textbook** | medium | curated_pure | title:principles_of, primo:no_record |
| 1998 | Systems Theory and Family Therapy: A Primer | 1982 | University Press of  | **textbook** | medium | curated_pure | default:no_signals, primo:no_record, google:textbook_subtitle |
| 673 | Diagnosing the System for Organizations | 1985 | Wiley | **textbook** | medium | curated_keyword | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 239 | Subjectivity, Information, Systems: Introduct | 1986 | Routledge | **textbook** | high | title_only | title:introduction_to, primo:no_record, google:textbook_subtitle |
| 1196 | Introduction to Modern Psychology: The Contro | 1990 | Control Systems Grou | **textbook** | high | curated_pure | title:introduction_to, primo:no_record |
| 2001 | Management Systems: Conceptual Considerations | 1990 | McGraw-Hill Higher E | **textbook** | medium | curated_pure | publisher:textbook_house, primo:no_record, openlibrary:anthology_subject |
| 437 | How Colleges Work: The Cybernetics of Academi | 1991 | John Wiley & Sons | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:no_record |
| 675 | Beyond Dispute: The Invention of Team Syntegr | 1994 | Wiley | **textbook** | medium | curated_keyword | publisher:textbook_house, primo:no_record |
| 193 | Brain of the Firm | 1995 | Wiley | **textbook** | medium | curated_pure | publisher:textbook_house, primo:no_record |
| 259 | Platform for Change | 1995 | Wiley | **textbook** | medium | curated_pure | publisher:textbook_house, primo:no_record |
| 215 | The Evolution of Ethics: An Introduction to C | 1999 | Dianic Publications | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record, google:textbook_subtitle |
| 447 | Facets of Systems Science | 2001 | Springer Science & B | **textbook** | high | curated_keyword | publisher:springer, desc:intro_text, primo:no_record |
| 386 | An Introduction to Systems Biology: Design Pr | 2006 | CRC Press | **textbook** | high | curated_pure | title:introduction_to, title:principles_of, primo:type_book→monograph |
| 1615 | Organizations as Complex Systems: An Introduc | 2006 | IAP | **textbook** | high | title_only | title:introduction_to, primo:no_record, google:textbook_subtitle |
| 1873 | Introduction to the History of Communication: | 2010 | Peter Lang | **textbook** | medium | curated_keyword | title:introduction_to, title:history_of, primo:no_record |
| 1997 | Controlling Uncertainty: Decision Making and  | 2010 | Wiley | **textbook** | medium | curated_pure | publisher:textbook_house, primo:no_record |
| 256 | Process Control A Practical Approach | 2011 | Wiley | **textbook** | medium | curated_pure | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 1249 | Pragmatics of Human Communication: A Study of | 2011 | W. W. Norton & Compa | **textbook** | medium | curated_pure | publisher:textbook_house, primo:no_record |
| 1250 | Change: Principles of Problem Formation and P | 2011 | W. W. Norton & Compa | **textbook** | high | curated_pure | title:principles_of, publisher:textbook_house, primo:no_record |
| 1379 | Fundamentals of Cybernetics | 2012 | Springer US, Boston, | **textbook** | high | title_only | title:fundamentals_of, publisher:springer, primo:type_web_resource |
| 1256 | Introduction to Systems Theory | 2013 | Polity | **textbook** | high | curated_pure | title:introduction_to, primo:no_record |
| 257 | Principles of Neural Design | 2015 | MIT Press | **textbook** | medium | curated_pure | title:principles_of, primo:type_book→monograph, primo:type_book→monograph |
| 286 | An Introduction to Cybernetics | 2015 | Martino Publishing | **textbook** | high | title_corroborated | title:introduction_to, primo:no_record |
| 1460 | Rise of the Machines: A Cybernetic History | 2016 | W. W. Norton & Compa | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:no_record |
| 1039 | Introduction to Anticipation Studies | 2017 | Springer | **textbook** | high | curated_pure | title:introduction_to, publisher:springer, primo:no_record |
| 362 | Content Analysis: An Introduction to Its Meth | 2018 | SAGE Publications | **textbook** | high | metadata_search | title:introduction_to, primo:type_book→monograph, primo:type_book→monograph |
| 422 | An Introduction to Cybernetic Synergy: Improv | 2021 | Taylor & Francis Lim | **textbook** | high | title_corroborated | title:introduction_to, primo:type_book→monograph, primo:type_book→monograph |
| 1259 | Unlocking Luhmann: A Keyword Introduction to  | 2021 | Bielefeld University | **textbook** | high | curated_pure | title:introduction_to, primo:type_book→monograph, primo:type_book→monograph |
| 1378 | Introduction to Cybersemiotics: A Transdiscip | 2021 | Springer Internation | **textbook** | high | curated_keyword | title:introduction_to, publisher:springer, primo:no_record |
| 1761 | Introduction to Systems Philosophy: Toward a  | 2021 | Taylor & Francis Gro | **textbook** | high | curated_pure | title:introduction_to, primo:no_record |
| 620 | Cyber-Physical Systems: Theory, Methodology,  | 2022 | John Wiley & Sons | **textbook** | medium | metadata_search | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 759 | Introduction to Safety Science: People, Organ | 2022 | CRC Press | **textbook** | high | curated_pure | title:introduction_to, primo:type_book→monograph, primo:type_book→monograph |
| 1017 | Ingenious Principles of Nature: Do We Reckon  | 2022 | Springer Fachmedien  | **textbook** | medium | curated_keyword | title:principles_of, publisher:springer, primo:no_record |
| 1601 | Designing Intelligent Construction Projects | 2022 | John Wiley & Sons | **textbook** | medium | curated_keyword | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 346 | Cybernetical Intelligence: Engineering Cybern | 2023 | John Wiley & Sons | **textbook** | medium | title_corroborated | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 378 | A Transdisciplinary Introduction to the World | 2023 | Springer Fachmedien  | **textbook** | high | title_corroborated | title:introduction_to, publisher:springer, primo:no_record |
| 1505 | Critical Systems Thinking: A Practitioner's G | 2024 | John Wiley & Sons | **textbook** | medium | curated_pure | publisher:textbook_house, primo:type_book→monograph, primo:type_book→monograph |
| 1896 | Minds and Machines | 1954 | Penguin Books | **popular** | medium | curated_keyword | publisher:trade_house, primo:no_record |
| 1894 | The Communication Systems of the Body | 1964 | Basic Books | **popular** | medium | curated_keyword | publisher:trade_house, primo:no_record |
| 674 | Management Science: The Business Use of Opera | 1968 | Doubleday | **popular** | medium | curated_keyword | publisher:trade_house, primo:no_record |
| 253 | Psycho-Cybernetics | 1969 | Pocket Books | **popular** | high | title_only | title:psycho_cyber, primo:no_record |
| 1838 | The Science of Mental Cybernetics | 1970 | Parker Publishing Co | **popular** | medium | title_only | default:no_signals, primo:no_record, google:cat_self_help |
| 430 | II Cybernetic Frontiers | 1974 | Random House | **popular** | medium | title_corroborated | publisher:trade_house, primo:no_record |
| 1864 | How to Use the Magic of Self-Cybernetics | 1974 | Littlefield, Adams | **popular** | medium | title_only | title:how_to, primo:no_record, google:cat_self_help |
| 1251 | How Real Is Real?: Confusion, Disinformation, | 1976 | Random House | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1458 | Hypno Cybernetics: Helping Yourself to a Rich | 1976 | Penguin Group (USA)  | **popular** | high | title_only | title:rich_life, publisher:trade_house, primo:no_record |
| 679 | Whole Earth Software Catalog 1986 | 1985 | Anchor | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 389 | Angels Fear: Towards an Epistemology of the S | 1988 | Bantam | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 576 | Freedom From Stress: Most People Deal With Sy | 1989 | Brandt Pub. | **popular** | medium | title_corroborated | default:no_signals, primo:no_record, google:cat_self_help |
| 677 | How Buildings Learn: What Happens After They' | 1995 | Penguin Books | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1826 | Structural Cybernetics: An Overview, How to B | 1995 | N. Dean Myer and Ass | **popular** | medium | title_corroborated | title:how_to, primo:no_record |
| 1217 | The Age of Spiritual Machines | 1998 | Penguin | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1236 | Perspectives on Behavioral Self-Regulation | 1999 | L. Erlbaum Asociates | **popular** | high | curated_pure | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 1500 | Full Circles Overlapping Lives: Culture and G | 2000 | Random House | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 172 | The Cyberiad: Stories | 2002 | HMH | **popular** | high | curated_keyword | default:no_signals, primo:no_record, google:cat_fiction |
| 1198 | People as Living Things: The Psychology of Pe | 2003 | Living Control Syste | **popular** | high | curated_pure | default:no_signals, primo:no_record, google:cat_self_help |
| 244 | R.U.R. (Rossum's Universal Robots) | 2004 | Penguin | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record, google:cat_fiction |
| 1216 | The Singularity Is Near: When Humans Transcen | 2005 | Penguin Books | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1199 | The Method of Levels: How to Do Psychotherapy | 2006 | Living Control Syste | **popular** | medium | curated_pure | title:how_to, primo:no_record |
| 680 | The Clock of the Long Now: Time and Responsib | 2008 | Basic Books | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 745 | Posthuman Metamorphosis: Narrative and System | 2008 | Fordham University P | **popular** | medium | curated_keyword | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 1197 | Management and Leadership: Insight for Effect | 2008 | Living Control Syste | **popular** | medium | curated_pure | default:no_signals, primo:no_record, google:cat_self_help |
| 324 | Dark Hero of the Information Age: In Search o | 2009 | Basic Books | **popular** | medium | title_corroborated | publisher:trade_house, primo:no_record |
| 676 | Whole Earth Discipline: Why Dense Cities, Nuc | 2010 | Penguin Publishing G | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1498 | Composing a Further Life: The Age of Active W | 2010 | Knopf Doubleday Publ | **popular** | medium | curated_pure | publisher:trade_house, desc:contributors, primo:no_record |
| 213 | The Information: A History, a Theory, a Flood | 2011 | Knopf Doubleday Publ | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1218 | How to Create a Mind: The Secret of Human Tho | 2012 | Viking | **popular** | medium | curated_pure | title:how_to, primo:no_record |
| 121 | Psycho-Cybernetics and Self-Fulfillment | 2013 | Igal Meirovich | **popular** | high | title_corroborated | title:psycho_cyber, desc:self_help, primo:no_record |
| 774 | Purposive Explanation in Psychology | 2013 | Harvard University P | **popular** | medium | curated_pure | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 264 | Our Robots, Ourselves: Robotics and the Myths | 2015 | Penguin | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 356 | Controlling People: The Paradoxical Nature of | 2015 | Australian Academic  | **popular** | medium | curated_pure | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 410 | Psycho-Cybernetics: Updated and Expanded | 2015 | Penguin | **popular** | high | title_corroborated | title:psycho_cyber, publisher:trade_house, desc:self_help |
| 337 | Ranulph Galnville and How to Live the Cyberne | 2016 |  | **popular** | medium | title_corroborated | title:how_to, primo:no_record |
| 1923 | Posthumanism and the Graphic Novel in Latin A | 2017 | UCL Press | **popular** | medium | curated_pure | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 258 | Possible Minds: Twenty-Five Ways of Looking a | 2019 | Penguin Press | **popular** | medium | curated_keyword | publisher:trade_house, primo:no_record |
| 1191 | A Foundational Explanation of Human Behavior: | 2021 | Amazon Digital Servi | **popular** | medium | curated_pure | title:how_to, primo:no_record, google:short_72pp |
| 235 | Success Cybernetics (Unabridged Edition) | 2022 | David De Angelis | **popular** | medium | title_corroborated | title:success, primo:no_record |
| 1609 | Repair: When and How to Improve Broken Object | 2022 | Springer Internation | **popular** | medium | curated_pure | title:how_to, publisher:springer, primo:no_record |
| 1525 | The Singularity Is Nearer: When We Merge With | 2024 | Penguin Publishing G | **popular** | medium | curated_pure | publisher:trade_house, primo:type_book→monograph, primo:type_book→monograph |
| 1608 | Feedback: How to Destroy or Save the World | 2024 | Springer Nature | **popular** | medium | curated_pure | title:how_to, publisher:springer, primo:type_book→monograph |
| 1943 | The Atomic Human: Understanding Ourselves in  | 2024 | Random House | **popular** | medium | curated_pure | publisher:trade_house, primo:no_record |
| 1731 | Posthumanism Meets Surveillance Capitalism: H | 2025 | Springer Nature Swit | **popular** | medium | curated_pure | title:how_to, publisher:springer, primo:no_record |
| 1747 | The Cybernetic Society: How Humans and Machin | 2025 | Basic Books | **popular** | medium | title_corroborated | publisher:trade_house, primo:no_record |
| 1934 | Psycho-Cybernetics 365: Thrive and Grow Every | 2025 | St. Martin's Publish | **popular** | high | title_corroborated | title:psycho_cyber, primo:no_record, google:cat_self_help |
| 1772 | Progress in Biocybernetics: Volume 1 | 1964 |  | **anthology** | high | curated_pure | title:volume_N, title:series_volume, primo:no_record |
| 446 | Embodiments of Mind | 1965 | M.I.T. Press | **anthology** | medium | curated_pure | default:no_signals, primo:no_record, openlibrary:anthology_subject |
| 1771 | Progress in Biocybernetics: Volume 2 | 1965 | Elsevier | **anthology** | high | curated_pure | title:volume_N, title:series_volume, primo:no_record |
| 1885 | Collected Papers of Jay W. Forrester | 1975 | Productivity Press | **anthology** | high | curated_pure | title:collected, primo:no_record, openlibrary:anthology_subject |
| 1779 | About Bateson: Essays on Gregory Bateson | 1977 | Dutton | **anthology** | high | curated_pure | title:essays_on, primo:no_record, google:anthology_subtitle |
| 349 | Cultures of the Future | 1978 | Mouton | **anthology** | medium | curated_pure | default:no_signals, primo:type_conference_proceeding, primo:type_book→monograph |
| 1381 | Sociocybernetics. An Actor-Oriented Social Sy | 1978 | Springer | **anthology** | high | curated_keyword | title:volume_N, title:series_volume, publisher:springer |
| 1382 | Sociocybernetics: An Actor-Oriented Social Sy | 1978 | Springer US | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 241 | Steps to an Ecology of Mind: Collected Essays | 1987 | Aronson | **anthology** | high | curated_pure | title:essays_on, title:collected, primo:no_record |
| 1786 | The Individual, Communication, and Society: E | 1989 | Cambridge University | **anthology** | high | curated_pure | title:essays_on, primo:type_book→monograph, primo:type_book→monograph |
| 187 | Norbert Wiener, 1894-1964 | 1990 | Springer | **anthology** | medium | curated_keyword | publisher:springer, desc:contributors, primo:type_book→monograph |
| 1260 | Essays on Self-Reference | 1990 | Columbia University  | **anthology** | high | curated_pure | title:essays_on, primo:type_book→monograph, primo:type_book→monograph |
| 1181 | How Many Grapes Went Into the Wine: Stafford  | 1994 | Wiley | **anthology** | medium | curated_pure | publisher:textbook_house, desc:edited_by, primo:no_record |
| 1087 | Signs of Meaning in the Universe | 1996 | Indiana University P | **anthology** | medium | curated_pure | desc:contributors, primo:type_book→monograph, primo:type_book→monograph |
| 1862 | Essays on Life Itself | 1999 | Columbia University  | **anthology** | high | curated_pure | title:essays_on, primo:type_book→monograph, primo:type_book→monograph |
| 177 | Understanding Understanding: Essays on Cybern | 2002 | Springer | **anthology** | high | title_corroborated | title:essays_on, publisher:springer, desc:contributors |
| 170 | Anticipatory Behavior in ALS: Foundations, Th | 2003 | Springer | **anthology** | medium | curated_pure | publisher:springer, primo:type_web_resource, primo:lcsh_anthology |
| 769 | Kybernetes the International Journal of Syste | 2005 | Emerald Group Publis | **anthology** | medium | title_only | title:series_volume, primo:type_book→monograph, primo:type_book→monograph |
| 1208 | Purpose, Meaning, and Action: Control Systems | 2007 | Palgrave Macmillan U | **anthology** | medium | curated_pure | desc:contributors, primo:type_book→monograph, primo:type_book→monograph |
| 229 | The Challenge of Anticipation: A Unifying Fra | 2008 | Springer Science & B | **anthology** | medium | curated_pure | publisher:springer, primo:type_web_resource, primo:contributors_no_creator |
| 236 | Systems Science and Cybernetics - Volume 3 | 2009 | EOLSS Publications | **anthology** | high | title_corroborated | title:volume_N, title:series_volume, primo:type_article |
| 312 | Emergence and Embodiment: New Essays on Secon | 2009 | Duke University Pres | **anthology** | high | curated_keyword | title:essays_on, primo:type_book→monograph, primo:type_book→monograph |
| 1263 | Autopoiesis in Organization Theory and Practi | 2009 | Emerald Publishing L | **anthology** | medium | curated_pure | default:no_signals, primo:type_web_resource, primo:contributors_no_creator |
| 1729 | Systems Science and Cybernetics - Volume 1 | 2009 | EOLSS Publications | **anthology** | high | title_corroborated | title:volume_N, title:series_volume, primo:type_article |
| 1730 | Systems Science and Cybernetics - Volume 2 | 2009 | EOLSS Publications | **anthology** | high | title_corroborated | title:volume_N, title:series_volume, primo:type_article |
| 1339 | Handbook of Personality and Self-Regulation | 2010 | Wiley-Blackwell | **anthology** | medium | curated_pure | title:handbook, publisher:textbook_house, primo:type_web_resource |
| 396 | Adaptation and Well-Being: Social Allostasis | 2011 | Cambridge University | **anthology** | medium | curated_pure | desc:contributors, primo:type_book→monograph, primo:type_book→monograph |
| 1728 | Fanged Noumena: Collected Writings 1987-2007 | 2011 | MIT Press | **anthology** | high | curated_pure | title:collected, primo:type_book→monograph, primo:type_book→monograph |
| 1739 | The Freudian Robot: Digital Media and the Fut | 2011 | University of Chicag | **anthology** | medium | curated_keyword | desc:contributors, primo:type_book→monograph, primo:type_book→monograph |
| 390 | Allostasis, Homeostasis, and the Costs of Phy | 2012 | Cambridge University | **anthology** | high | curated_pure | desc:edited_by, primo:no_record |
| 1247 | Theory of Society, Volume 1 | 2012 | Stanford University  | **anthology** | high | curated_pure | title:volume_N, title:series_volume, primo:type_book→monograph |
| 1346 | When Things Go Wrong | 2012 | Routledge | **anthology** | high | curated_keyword | desc:edited_by, primo:no_record |
| 1918 | A More Developed Sign: Interpreting the Work  | 2012 | Tartu University Pre | **anthology** | medium | curated_pure | default:no_signals, primo:type_web_resource, primo:contributors_no_creator |
| 1248 | Theory of Society, Volume 2 | 2013 | Stanford University  | **anthology** | high | curated_pure | title:volume_N, title:series_volume, primo:type_book→monograph |
| 1347 | The Transhumanist Reader: Classical and Conte | 2013 | John Wiley & Sons | **anthology** | medium | curated_pure | title:essays_on, title:reader, publisher:textbook_house |
| 392 | Alleys of Your Mind: Augmented Intelligence a | 2015 | Meson Press | **anthology** | medium | curated_keyword | default:no_signals, primo:type_web_resource, primo:contributors_no_creator |
| 1115 | Anticipation Across Disciplines | 2015 | Springer | **anthology** | medium | curated_pure | publisher:springer, desc:contributors, primo:no_record |
| 1344 | Communication and Control: Tools, Systems, an | 2015 | Lexington Books | **anthology** | high | curated_keyword | desc:edited_by, primo:type_book→monograph, primo:type_book→monograph |
| 185 | Systems, Cybernetics, Control, and Automation | 2017 | River Publishers | **anthology** | medium | title_corroborated | desc:contributors, primo:type_book→monograph, primo:type_book→monograph |
| 371 | Beyond machines of loving grace: Hacker cultu | 2018 | Edições Sesc | **anthology** | high | title_only | desc:edited_by, primo:no_record |
| 1920 | Verhaltensdesign: Technologische und ästhetis | 2018 | Transcript | **anthology** | high | curated_keyword | default:no_signals, primo:type_web_resource, primo:contributors_no_creator |
| 1135 | The Viability of Organizations Vol. 1: Decodi | 2019 | Springer Internation | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 1136 | The Viability of Organizations Vol. 2: Diagno | 2019 | Springer Internation | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 1137 | The Viability of Organizations Vol. 3: Design | 2019 | Springer Internation | **anthology** | high | curated_keyword | title:vol_N, title:series_volume, publisher:springer |
| 2002 | Norbert Wiener - a Mathematician Among Engine | 2022 | World Scientific | **anthology** | medium | curated_keyword | desc:contributors, primo:no_record |
| 1179 | Cybernetics and the Origin of Information | 2023 | Rowman & Littlefield | **anthology** | medium | title_corroborated | desc:contributors, primo:type_book→monograph, primo:type_book→monograph |
| 1351 | Cybernetics for the 21st Century Vol. 1: Epis | 2024 | Hanart Press | **anthology** | high | title_corroborated | title:vol_N, title:series_volume, primo:no_record |
| 1114 | Gregory Bateson: The Legacy of a Scientist | 1982 | Beacon Press | **history_bio** | high | curated_pure | title:legacy_of, desc:biography, primo:no_record |
| 1501 | With a Daughter's Eye: A Memoir of Margaret M | 1984 | W. Morrow | **history_bio** | high | curated_pure | title:memoir, desc:memoir, primo:type_book→monograph |
| 223 | The Cybernetics Group | 1991 | MIT Press | **history_bio** | high | title_corroborated | desc:biography, primo:type_book→monograph, primo:type_book→monograph |
| 303 | From Newspeak to Cyberspeak: A History of Sov | 2002 | MIT Press | **history_bio** | high | title_corroborated | title:history_of, primo:no_record |
| 1182 | Stafford Beer: A Personal Memoir - Includes a | 2003 | Wavestone Press | **history_bio** | high | curated_keyword | title:memoir, primo:no_record, google:short_64pp |
| 1083 | Digital Performance: A History of New Media i | 2007 | MIT Press | **history_bio** | high | curated_pure | title:history_of, primo:type_book→monograph, primo:type_book→monograph |
| 199 | Understanding Gregory Bateson: Mind, Beauty,  | 2008 | SUNY Press | **history_bio** | high | curated_keyword | desc:biography, primo:type_book→monograph, primo:type_book→monograph |
| 1685 | Biosemiotics: An Examination Into the Signs o | 2008 | University of Scrant | **history_bio** | high | curated_pure | title:life_of, primo:no_record |
| 1703 | Systems Thinkers | 2009 | Springer London | **history_bio** | high | curated_pure | publisher:springer, desc:biography, primo:type_book→monograph |
| 1207 | Cybernethisms: Aldo Giorgini's Computer Art L | 2015 | Purdue University Pr | **history_bio** | high | curated_pure | desc:biography, primo:type_book→monograph, primo:type_book→monograph |
| 1767 | Beautiful Data: A History of Vision and Reaso | 2015 | Duke University Pres | **history_bio** | high | curated_keyword | title:history_of, primo:type_other, primo:type_book→monograph |
| 176 | Upside-Down Gods: Gregory Bateson's World of  | 2016 | Fordham Univ Press | **history_bio** | high | curated_pure | desc:biography, primo:type_web_resource |
| 293 | How Not to Network a Nation: The Uneasy Histo | 2016 | MIT Press | **history_bio** | high | curated_keyword | title:history_of, primo:no_record |
| 1315 | Staying With the Trouble: Making Kin in the C | 2016 | Duke University Pres | **history_bio** | high | curated_pure | desc:biography, desc:memoir, primo:type_other |
| 295 | How Emotions Are Made: The Secret Life of the | 2017 | Houghton Mifflin Har | **history_bio** | high | curated_pure | title:life_of, primo:no_record |
| 299 | Harmonies of Disorder: Norbert Wiener: A Math | 2017 | Springer Internation | **history_bio** | high | curated_keyword | publisher:springer, desc:biography, primo:no_record |
| 408 | Runaway: Gregory Bateson, the Double Bind, an | 2017 | University of North  | **history_bio** | high | curated_pure | desc:biography, primo:no_record |
| 272 | Norbert Wiener-A Life in Cybernetics: Ex-Prod | 2018 | MIT Press | **history_bio** | high | title_corroborated | title:life_of, primo:type_book→monograph, primo:type_book→monograph |
| 1956 | Communication Theory Through the Ages | 2019 | Routledge | **history_bio** | high | curated_pure | desc:biography, primo:type_book→monograph, primo:type_book→monograph |
| 296 | History of Computer Art | 2020 | Lulu Press, Incorpor | **history_bio** | high | curated_keyword | title:history_of, primo:no_record |
| 1581 | Whole Earth: The Many Lives of Stewart Brand | 2022 | Penguin Publishing G | **history_bio** | medium | curated_pure | publisher:trade_house, desc:biography, primo:no_record |
| 1041 | The Eye of the Master: A Social History of Ar | 2023 | Verso | **history_bio** | high | curated_pure | title:history_of, primo:no_record |
| 1349 | Return to China One Day: The Learning Life of | 2023 | Springer | **history_bio** | high | curated_pure | title:life_of, publisher:springer, primo:type_book→monograph |
| 1750 | A History of Artificially Intelligent Archite | 2023 | Routledge/Taylor & F | **history_bio** | high | curated_keyword | title:history_of, primo:type_book→monograph, primo:type_book→monograph |
| 1400 | The Unaccountability Machine | 2024 | Profile Books Limite | **history_bio** | high | curated_keyword | desc:biography, primo:type_book→monograph, primo:type_book→monograph |
| 1723 | An Artificial History of Natural Intelligence | 2024 | University of Chicag | **history_bio** | high | curated_pure | title:history_of, primo:type_book→monograph, primo:type_book→monograph |
| 1936 | Burning Down the House: Talking Heads and the | 2025 | HarperCollins Publis | **history_bio** | medium | curated_pure | desc:contributors, desc:biography, primo:no_record |
| 1271 | The Way Things Work Book of the Computer: An  | 1974 | Simon and Schuster | **handbook** | high | title_corroborated | title:encyclopedia, primo:no_record |
| 189 | International Encyclopedia of Systems and Cyb | 1997 | K.G. Saur | **handbook** | high | title_corroborated | title:encyclopedia, primo:type_review, primo:type_journal |
| 1206 | International Handbook of Semiotics | 2015 | Springer | **handbook** | high | curated_pure | title:handbook, publisher:springer, primo:type_book→monograph |
| 203 | The Routledge Handbook of Philosophy of Infor | 2016 | Routledge, Taylor &  | **handbook** | high | curated_pure | title:handbook, primo:type_book→monograph, primo:type_book→monograph |
| 298 | Handbook of Research on Applied Cybernetics a | 2017 | IGI Global | **handbook** | high | title_corroborated | title:handbook, primo:no_record |
| 1753 | The Routledge Handbook of Soft Power | 2017 | Routledge | **handbook** | high | curated_pure | title:handbook, primo:type_book→monograph, primo:type_book→monograph |
| 181 | The Interdisciplinary Handbook of Perceptual  | 2020 | Elsevier Science | **handbook** | medium | curated_pure | title:handbook, desc:biography, primo:no_record |
| 300 | Handbook of Anticipation: Theoretical and App | 2020 | Springer Internation | **handbook** | high | curated_pure | title:handbook, publisher:springer, primo:no_record |
| 1950 | A Silvan Tomkins Handbook: Foundations for Af | 2020 | University of Minnes | **handbook** | high | curated_pure | title:handbook, primo:type_book→monograph, primo:type_book→monograph |
| 1131 | Handbook of Systems Sciences | 2021 | Springer Nature Sing | **handbook** | high | curated_pure | title:handbook, publisher:springer, primo:type_book→monograph |
| 1602 | The Sage Handbook of Human-Machine Communicat | 2023 | SAGE | **handbook** | high | curated_pure | title:handbook, primo:type_book→monograph, primo:type_book→monograph |
| 1724 | Handbook of Emotion Regulation | 2024 | Guilford Publication | **handbook** | high | curated_pure | title:handbook, primo:type_book→monograph, primo:type_book→monograph |
| 1884 | Urban Dynamics: Extensions and Reflections | 1972 | San Francisco Press | **proceedings** | medium | curated_pure | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 351 | Current Topics in Cybernetics and Systems: Pr | 1978 | Springer | **proceedings** | high | title_only | title:proceedings, publisher:springer, primo:no_record |
| 1842 | Communication and Control in Society | 1979 | CRC Press | **proceedings** | medium | curated_keyword | default:no_signals, primo:no_record, openlibrary:proceedings_subject |
| 1801 | Science of Goal Formulation | 1990 | CRC Press | **proceedings** | high | curated_keyword | desc:proceedings, primo:no_record |
| 267 | Our Own Metaphor: A Personal Account of a Con | 2004 | Hampton Pr | **proceedings** | high | curated_pure | title:conference_on, primo:no_record, openlibrary:proceedings_subject |
| 384 | Anticipatory Behavior in Adaptive Learning Sy | 2009 | Springer | **proceedings** | high | curated_pure | publisher:springer, desc:proceedings, primo:type_web_resource |
| 443 | Cybernetics and Systems ’86: Proceedings of t | 2011 | Springer | **proceedings** | high | title_corroborated | title:proceedings, publisher:springer, desc:proceedings |
| 1705 | Systems Thinking in Europe | 2012 | Springer US | **proceedings** | high | metadata_search | publisher:springer, desc:proceedings, primo:type_book→monograph |
| 328 | Cybernetics: State of the Art | 2017 | Universitätsverlag d | **proceedings** | medium | title_corroborated | default:no_signals, primo:no_record, openlibrary:proceedings_subject |
| 418 | Cybernetics and Systems: Social and Business  | 2018 | Routledge | **proceedings** | medium | title_corroborated | default:no_signals, primo:type_book→monograph, primo:type_book→monograph |
| 1038 | Anticipation, Agency and Complexity | 2019 | Springer | **proceedings** | high | curated_pure | publisher:springer, desc:proceedings, primo:no_record |
| 917 | Seconde cybernétique et complexité: Rencontre | 2022 | Editions L'Harmattan | **proceedings** | medium | curated_pure | default:no_signals, primo:no_record, openlibrary:proceedings_subject |
| 1749 | Russian-English dictionary and reader in the  | 1966 | Academic Press | **reader** | medium | curated_pure | title:reader, title:bibliography, primo:no_record |
| 1195 | Living Control Systems: Selected Papers of Wi | 1989 | Control Systems Grou | **reader** | high | curated_pure | title:selected, primo:no_record |
| 1774 | Living Control Systems II: Selected Papers of | 1992 |  | **reader** | high | curated_pure | title:selected, primo:no_record |
| 1021 | A Stanislaw Lem Reader | 1997 | Northwestern Univers | **reader** | high | curated_pure | title:reader, primo:no_record, google:cat_fiction |
| 190 | Information: A Reader | 2022 | Columbia University  | **reader** | high | curated_pure | title:reader, primo:type_book→monograph, primo:type_book→monograph |
| 1988 | Basic and Applied General Systems Research: A | 1985 | Hemisphere Publishin | **report** | high | curated_pure | title:bibliography, primo:no_record |
| 1951 | Sensing and Making Sense: Photosensitivity an | 2021 | Transcript | **report** | high | curated_keyword | default:no_signals, primo:type_dissertation→report, primo:type_dissertation→report |