"""Prompt templates for LLM generation"""

TOPIC_GENERATION_PROMPT = """You are a documentary topic researcher for a channel that covers WILD history — the strange, bizarre, intense, and little-known stories that actually happened. Generate exactly {num_topics} compelling documentary topics for long-form YouTube content (12-18 minutes).

CRITICAL: Each topic MUST be a real, verifiable event/person/phenomenon with its OWN EXISTING Wikipedia article. Do NOT invent or fabricate. Every single topic must have enough documented material for 12+ minutes of content.

What we want:
- Wild, intense, or bizarre true stories that feel unbelievable but are 100% real
- Events with high stakes, dramatic tension, or shocking twists
- Obscure history that most people have never heard of
- Tales of survival, disaster, eccentric geniuses, forgotten catastrophes, strange phenomena
- History Channel energy but factual — think "this actually happened and it's insane"

What to AVOID:
- Overdone topics (World War II, Hitler, Titanic, JFK, moon landing, etc.)
- Boring or academic subjects with no narrative hook
- Vague concepts — each topic needs a specific event or person
- Anything pseudoscientific or unverifiable

Respond ONLY with a valid JSON object containing a "topics" array. No preamble, no explanation, no markdown.

Example output:
{{
  "topics": [
    {{
      "title": "Great Molasses Flood",
      "description": "On January 15, 1919, a 50-foot wave of molasses swept through Boston's North End at 35 mph, killing 21 people. The cause? A poorly built tank, warm weather, and catastrophic negligence. This documentary examines the disaster, the survivors' stories, and the legal landmark it created."
    }},
    {{
      "title": "The Dancing Plague of 1518",
      "description": "In July 1518, a woman in Strasbourg began dancing uncontrollably in the streets. Within a week, 30 others joined her. Within a month, hundreds were dancing until they collapsed, some dancing themselves to death. Over 400 people were affected. The cause remains unknown to this day."
    }},
    {{
      "title": "The Tunguska Event",
      "description": "In 1908, a massive explosion flattened 800 square miles of Siberian forest with the force of 1,000 Hiroshima bombs. No impact crater was ever found. Over a century later, scientists still debate whether it was an asteroid, a comet, or something far stranger."
    }}
  ]
}}

Generate exactly {num_topics} wild history topics now:"""


WEIRD_HISTORY_PROMPT = """You are a documentary topic researcher specializing in the WEIRDEST true stories from history. Generate exactly {num_topics} documentary topics for long-form YouTube content (12-18 minutes).

CRITICAL: Each topic MUST be a real, verifiable event/person with its OWN EXISTING Wikipedia article. Do NOT invent. Every topic must have enough documented material.

What we want:
- The strangest, most bizarre true stories from history
- Events so weird they sound fake but are thoroughly documented
- Medical anomalies, mass hysteria events, forgotten catastrophes
- Eccentric figures whose real lives are stranger than fiction
- Bizarre coincidences, odd scientific discoveries, weird cultural phenomena

Avoid: overdone topics, pseudoscience, aliens, ghosts, mainstream conspiracy theories

Respond ONLY with valid JSON. No preamble.

Example output:
{{
  "topics": [
    {{
      "title": "Dancing plague of 1518",
      "description": "In July 1518, a woman named Frau Troffea began dancing fervently in the streets of Strasbourg. Within a month, hundreds of people were dancing uncontrollably, some dancing themselves to death. No one knows why. Theories range from mass psychogenic illness to ergot poisoning, but the true cause remains a mystery."
    }},
    {{
      "title": "The Great Stink of 1858",
      "description": "In the summer of 1858, the smell from the River Thames became so unbearable that the British Parliament had to abandon its chambers drenched in chlorinated lime. This documentary explores how a literal stench — caused by 2 million tons of raw sewage — forced the modernization of London's entire sewer system."
    }},
    {{
      "title": "Emperor Norton I",
      "description": "In 1859, Joshua Abraham Norton, a bankrupt San Francisco businessman, declared himself Emperor of the United States and Protector of Mexico. Remarkably, the city of San Francisco humored him for 21 years. He issued his own currency, dissolved Congress by decree, and when he died, 30,000 people attended his funeral."
    }}
  ]
}}

Generate exactly {num_topics} weird history topics now:"""


TRUE_CRIME_PROMPT = """You are a documentary topic researcher specializing in TRUE CRIME stories from history — high-profile crimes, unsolved murders, serial killers, heists, and forensic breakthroughs that changed justice forever. Generate exactly {num_topics} documentary topics for long-form YouTube content (12-18 minutes).

CRITICAL: Each topic MUST be a real, documented crime with its OWN EXISTING Wikipedia article. Do NOT invent. Every topic must have enough documented evidence to sustain 12+ minutes.

What we want:
- Notorious true crime cases with substantial investigation records and trial transcripts
- Murder mysteries, cold cases, and forensic breakthroughs with real evidence
- Famous heists, art thefts, and bank robberies with dramatic details
- Serial killer cases with unique MOs or investigative innovations
- Crimes that changed laws, policing, or forensic science forever
- Wrongful conviction cases where new evidence overturned verdicts

What to AVOID:
- Overdone cases (Jack the Ripper, Lizzie Borden, Black Dahlia unless a fresh angle)
- Speculative theories without evidence
- Cases with no resolution or too little documentation for 12+ minutes
- Fictional or supernatural explanations

Respond ONLY with valid JSON. No preamble.

Example output:
{{
  "topics": [
    {{
      "title": "The Tylenol Murders",
      "description": "In 1982, seven people in the Chicago area died after taking Extra-Strength Tylenol capsules laced with cyanide. The culprit was never caught, but the case revolutionized product safety forever — introducing tamper-evident packaging that we still use today. This documentary explores the murders, the manhunt, and how one unsolved case changed consumer protection worldwide."
    }},
    {{
      "title": "D.B. Cooper",
      "description": "On November 24, 1971, a man calling himself Dan Cooper hijacked Northwest Orient Flight 305, collected a $200,000 ransom, then parachuted into the Pacific Northwest night. Despite one of the largest manhunts in FBI history and a 2024 breakthrough in parachute evidence, his identity remains a mystery after 50+ years."
    }},
    {{
      "title": "The Murder of Emmett Till",
      "description": "In 1955, 14-year-old Emmett Till was brutally murdered in Mississippi for allegedly whistling at a white woman. His mother's decision to hold an open-casket funeral galvanized the civil rights movement. This documentary examines the crime, the trial that shocked the nation, and how one boy's murder helped change America."
    }}
  ]
}}

Generate exactly {num_topics} true crime topics now:"""


MYSTERY_PROMPT = """You are a documentary topic researcher specializing in real historical mysteries and unsolved cases that have genuine documentation. Generate exactly {num_topics} documentary topics for long-form YouTube content (12-18 minutes).

CRITICAL: Each topic MUST be a real, documented mystery with its OWN EXISTING Wikipedia article. Do NOT invent. Every topic must have enough documented evidence to sustain 12+ minutes.

What we want:
- Genuine unsolved mysteries with substantial documentation and investigation
- Cold cases that have real evidence, multiple theories, and ongoing research
- Unexplained archaeological discoveries that challenge conventional history
- Disappearances, cryptologic puzzles, and forensic mysteries with paper trails
- Mysteries where new evidence has emerged in recent years

What to AVOID:
- Aliens, Bigfoot, ghosts, psychic phenomena, or pseudoscience
- The Bermuda Triangle, Atlantis, or any overdone mystery
- Topics with no verifiable evidence or documentation
- Conspiracy theories without factual basis

Respond ONLY with valid JSON. No preamble.

Example output:
{{
  "topics": [
    {{
      "title": "Tamam Shud case",
      "description": "In 1948, a well-dressed man was found dead on Somerton Park beach in Australia. In his pocket was a scrap of paper reading 'Tamám Shud' — Persian for 'it is finished.' His identity, cause of death, and the meaning of the cryptic clue remain unknown despite decades of investigation, codebreaking attempts, and an exhumation in 2021."
    }},
    {{
      "title": "Lead Masks case",
      "description": "In 1966, two electrical engineers were found dead on a hill in Brazil, wearing lead masks that covered their eyes. Beside them were instructions for using the masks and a notebook with cryptic notes. Despite multiple autopsy findings and decades of investigation, the case has never been solved."
    }},
    {{
      "title": "The Mary Celeste",
      "description": "In 1872, the brigantine Mary Celeste was discovered adrift and perfectly intact in the Atlantic Ocean. The cargo was untouched, the lifeboat was gone, and the ten crew members were never seen again. No distress signal, no storm damage, no explanation — the most famous ghost ship in history remains an open question."
    }}
  ]
}}

Generate exactly {num_topics} historical mystery topics now:"""


SCRIPT_GENERATION_PROMPT_TEMPLATE = """You are a documentary scriptwriter. Write a compelling, ready-to-narrate documentary script for the following topic.

Topic: {topic_title}
Description: {topic_description}

Research facts to incorporate:
{research_facts}

CRITICAL RULES - READ CAREFULLY:
1. WORD COUNT IS THE MOST IMPORTANT REQUIREMENT: The script MUST be 3000-4500 words total. Each section MUST be 400-600 words of narration. Count your words as you write. If a section has fewer than 400 words, keep writing. Short scripts will be rejected.
2. NEVER use placeholder text like "[insert image here]", "[archival photo goes here]", "[show footage]", or any generic brackets. Every [VISUAL: ...] marker MUST contain a specific, descriptive visual concept.
3. Write as if this script will be read directly by a narrator - no meta-instructions or stage directions.
4. Write expansively — use vivid descriptions, historical context, thorough explanations, background details, and multiple specific examples per point. Each paragraph should be 3-5 sentences. Each section should have 5-8 paragraphs.

Structure requirements:
- Begin with a strong narrative hook — the first paragraph must grab viewer attention
- 5-8 distinct sections, each with a clear focus
- Include specific facts, dates, figures, and quotes where relevant
- Written for a general audience (avoid jargon, or explain it)
- End with a reflective conclusion that ties back to the hook
- Use substantial detail from the research facts — expand on each point with context

Allowed formatting ONLY:
- [VISUAL: specific visual description]
- [NARRATOR:]
- [SECTION: title]

Write the full script now for "{topic_title}". Remember: 3000-4500 words total, 400-600 words per section. Do NOT stop after just a hook — write the ENTIRE script from hook through all sections to conclusion. Begin:"""
