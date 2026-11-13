type OfflineConcept = {
  id: string;
  name: string;
  aliases: string[];
  definition: string;
  purpose: string;
  mechanism: string;
  analogy: string;
  summary: string;
};

const concepts: OfflineConcept[] = [
  {
    id: "transformer",
    name: "Transformer",
    aliases: ["transformer", "transformers"],
    definition: "A transformer transfers electrical energy between circuits using electromagnetic induction.",
    purpose: "It is commonly used to step AC voltage up or down; it does not change the supply frequency.",
    mechanism: "An alternating current in one winding creates a changing magnetic field that induces voltage in another winding.",
    analogy: "You can think of it as a voltage adapter for AC power, without treating it as a plug adapter or a product specification.",
    summary: "transfers AC energy between circuits and can change voltage",
  },
  {
    id: "generator",
    name: "Generator",
    aliases: ["generator", "generators", "genset", "gensets"],
    definition: "A generator converts mechanical energy into electrical energy.",
    purpose: "It can provide electrical power from a mechanical source when that source is running.",
    mechanism: "A prime mover turns part of the generator, inducing electrical output in its windings.",
    analogy: "It is a little like a bicycle dynamo: motion is converted into electrical output, though real generators are much more complex.",
    summary: "produces electrical energy from mechanical input",
  },
  {
    id: "inverter",
    name: "Inverter",
    aliases: ["inverter", "inverters"],
    definition: "An inverter converts direct current (DC) into alternating current (AC).",
    purpose: "It lets DC sources, such as batteries or solar systems, supply AC equipment when the system is designed for that use.",
    mechanism: "Power electronics switch the DC input to synthesize an AC output; the output characteristics depend on the inverter design.",
    analogy: "Think of it as a current-format converter, not as a source of energy by itself.",
    summary: "converts DC input into AC output",
  },
  {
    id: "battery",
    name: "Battery",
    aliases: ["battery", "batteries", "battery storage", "energy storage"],
    definition: "A battery stores energy chemically and releases it as electrical energy.",
    purpose: "It can store energy for later use; capacity describes stored energy, while power describes how quickly energy can be delivered.",
    mechanism: "Electrochemical reactions move electrons through an external circuit while ions move inside the cell.",
    analogy: "Capacity is like the size of a water tank, while power is like the width of its outlet; that analogy is only a way to distinguish the terms.",
    summary: "stores energy and supplies electrical power later",
  },
  {
    id: "solar",
    name: "Solar panel",
    aliases: ["solar panel", "solar panels", "photovoltaic panel", "photovoltaic panels", "photovoltaic module", "pv panel", "pv panels", "solar module"],
    definition: "A solar panel uses photovoltaic cells to convert sunlight into direct-current (DC) electricity.",
    purpose: "It provides electrical energy from sunlight, usually as part of a larger system with suitable conversion and controls.",
    mechanism: "Light interacting with semiconductor cells creates electrical current.",
    analogy: "It is a sunlight-to-electricity source; it is not the same component as an inverter or a battery.",
    summary: "converts sunlight into DC electrical energy",
  },
  {
    id: "ats",
    name: "Automatic transfer switch (ATS)",
    aliases: ["automatic transfer switch", "transfer switch", "ats"],
    definition: "An automatic transfer switch (ATS) switches a load between available power sources.",
    purpose: "It is commonly used to transfer a supported load between a utility supply and a standby source.",
    mechanism: "Its controls monitor configured sources and operate switching equipment according to the system design.",
    analogy: "It is a source selector, not a generator: it switches between supplies but does not create power.",
    summary: "switches a load between power sources",
  },
  {
    id: "breaker",
    name: "Circuit breaker",
    aliases: ["circuit breaker", "circuit breakers", "breaker", "breakers"],
    definition: "A circuit breaker is a protective switching device designed to interrupt current under specified abnormal conditions.",
    purpose: "It helps protect an electrical circuit when conditions exceed the device's designed limits.",
    mechanism: "A sensing and trip mechanism opens the circuit when its particular operating criteria are met.",
    analogy: "It is a resettable protective switch, but its correct selection and operation depend on the installation.",
    summary: "interrupts a circuit under specified abnormal conditions",
  },
  {
    id: "voltage",
    name: "Voltage",
    aliases: ["voltage", "potential difference"],
    definition: "Voltage is the electrical potential difference between two points, measured in volts (V).",
    purpose: "It describes the electrical potential that can drive current through a circuit.",
    mechanism: "A source maintains a difference in electric potential between its terminals.",
    analogy: "In a simple water analogy, voltage is similar to pressure; it is not the same thing as current.",
    summary: "electrical potential difference, measured in volts",
  },
  {
    id: "current",
    name: "Current",
    aliases: ["electric current", "current", "amperage"],
    definition: "Electric current is the rate at which electric charge flows, measured in amperes (A).",
    purpose: "It describes how much charge is flowing through a circuit over time.",
    mechanism: "When a circuit is complete and a potential difference is present, charge carriers move through the circuit.",
    analogy: "In a simple water analogy, current is similar to flow rate; it is different from voltage.",
    summary: "the rate of electric charge flow, measured in amperes",
  },
  {
    id: "power",
    name: "Electrical power",
    aliases: ["electrical power", "power"],
    definition: "Electrical power is the rate at which electrical energy is transferred or converted, measured in watts (W).",
    purpose: "It describes the rate of energy use or delivery at a particular moment.",
    mechanism: "In a simple DC circuit, power is voltage multiplied by current; AC calculations can also depend on power factor.",
    analogy: "Power is like the rate of spending, while energy is the total amount spent over time.",
    summary: "the rate of electrical energy transfer, measured in watts",
  },
  {
    id: "energy",
    name: "Electrical energy",
    aliases: ["electrical energy", "energy", "kilowatt hour", "kilowatt hours", "kwh"],
    definition: "Electrical energy is the amount of work or energy transferred over time.",
    purpose: "It describes total consumption or storage; kilowatt-hours (kWh) are a common energy unit.",
    mechanism: "For steady power, energy is power multiplied by time.",
    analogy: "If power is the rate of spending, energy is the total amount spent.",
    summary: "the total amount of electrical work transferred over time",
  },
  {
    id: "frequency",
    name: "Frequency",
    aliases: ["frequency", "hertz"],
    definition: "Frequency is the number of cycles per second in a repeating signal, measured in hertz (Hz).",
    purpose: "It describes how quickly an AC waveform repeats.",
    mechanism: "A frequency of one hertz means one cycle occurs each second.",
    analogy: "It is like the cadence of a repeating beat; it is separate from voltage magnitude.",
    summary: "the number of signal cycles per second, measured in hertz",
  },
  {
    id: "power-factor",
    name: "Power factor",
    aliases: ["power factor", "pf"],
    definition: "Power factor describes how effectively apparent power is converted into useful real power in an AC system.",
    purpose: "It helps characterize AC loads and is relevant to how electrical capacity is used.",
    mechanism: "For a simple sinusoidal system, it relates real power to apparent power; the exact interpretation depends on the waveform and system.",
    analogy: "It is a useful-effort-to-total-effort ratio, though real installations may need a more detailed analysis.",
    summary: "how real power relates to apparent power in an AC system",
  },
  {
    id: "efficiency",
    name: "Efficiency",
    aliases: ["efficiency", "conversion efficiency"],
    definition: "Efficiency is the ratio of useful output energy or power to input energy or power, usually expressed as a percentage.",
    purpose: "It indicates how much input becomes useful output rather than losses.",
    mechanism: "Efficiency is calculated as useful output divided by input, using comparable quantities and conditions.",
    analogy: "If a device is 90% efficient under a stated test condition, about 90% of the measured input becomes useful output under that condition.",
    summary: "the useful output divided by the input, often expressed as a percentage",
  },
];

type OfflineReply = {
  id: string;
  role: "assistant";
  content: string;
  tool_executed: "offline_response";
  confidence: "low";
  warnings: string[];
};

function normalize(text: string): string {
  return text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
}

function conceptsInQuery(query: string): OfflineConcept[] {
  const normalized = ` ${normalize(query)} `;
  const matches = concepts.flatMap((concept) =>
    concept.aliases.flatMap((alias) => {
      const term = normalize(alias);
      const index = normalized.indexOf(` ${term} `);
      return index < 0 ? [] : [{ concept, index, length: term.length }];
    }),
  );
  matches.sort((a, b) => a.index - b.index || b.length - a.length);

  const found = new Set<string>();
  return matches
    .filter(({ concept }) => {
      if (found.has(concept.id)) return false;
      found.add(concept.id);
      return true;
    })
    .map(({ concept }) => concept);
}

function comparisonSummary(first: OfflineConcept, second: OfflineConcept): string {
  const pair = new Set([first.id, second.id]);
  if (pair.has("voltage") && pair.has("current")) {
    return "Voltage is potential difference (V); current is charge flow (A). They describe different properties and are not interchangeable.";
  }
  if (pair.has("power") && pair.has("energy")) {
    return "Power is the rate of energy transfer (W); energy is the amount transferred over time (often kWh).";
  }
  if (pair.has("generator") && pair.has("inverter")) {
    return "A generator produces electrical energy from mechanical input; an inverter converts DC electricity into AC. They perform different jobs and are not direct substitutes.";
  }
  if (pair.has("solar") && pair.has("inverter")) {
    return "A solar panel converts sunlight into DC electricity; an inverter converts DC into AC. They are different components that may work together in a system.";
  }
  if (pair.has("generator") && pair.has("battery")) {
    return "A generator produces electricity while driven by a mechanical source; a battery stores energy for later delivery. Their roles and operating constraints differ.";
  }
  if (pair.has("transformer") && pair.has("inverter")) {
    return "A transformer transfers AC energy between circuits and can change voltage; an inverter converts DC into AC. They solve different conversion tasks.";
  }
  if (pair.has("ats") && pair.has("breaker")) {
    return "An ATS selects between power sources; a circuit breaker protects and can interrupt a circuit under specified conditions. They are not interchangeable.";
  }
  return `${first.name} ${first.summary}; ${second.name.toLowerCase()} ${second.summary}. Their roles are different, even when both are used in the same electrical system.`;
}

function makeReply(content: string): OfflineReply {
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content,
    tool_executed: "offline_response",
    confidence: "low",
    warnings: ["Curated offline guidance; not AI-generated.", "No catalogue or manual sources were used."],
  };
}

export function offlineReply(query: string, hasAttachments = false): OfflineReply {
  const normalized = normalize(query);
  if (hasAttachments) {
    return makeReply(
      "I can’t inspect attachments in offline mode or confirm whether they reached the service. Check the service before retrying; avoid resending sensitive files until you know whether they were received.",
    );
  }

  if (/^(hi|hello|hey|good morning|good afternoon|good evening)$/.test(normalized)) {
    return makeReply(
      "Hello! I can help with general electrical concepts and comparisons while offline. For example, ask how an inverter works or how voltage differs from current. I can’t look up Jenga products or live information.",
    );
  }
  if (/\b(help|what can you do|how do you work|what do you know)\b/.test(normalized)) {
    return makeReply(
      "I can explain common electrical concepts, describe their general purpose, and compare terms such as voltage vs current or generator vs inverter. I can’t access accounts, manuals, attachments, Jenga product specifications, prices, or availability, and I can’t give equipment-specific repair or safety instructions.",
    );
  }
  if (/\b(fault|troubleshoot|alarm|repair|unsafe|safety|emergency|smoke|shock|overheat|overheating|short circuit)\b/.test(normalized)) {
    return makeReply(
      "I can’t assess faults or provide equipment-specific safety or repair guidance while offline. If there may be immediate danger, keep clear and follow your site’s emergency procedure; contact a qualified professional. Use the manufacturer’s manual for the exact equipment.",
    );
  }
  if (/\b(prices?|costs?|quotes?|pricing|availability|in stock|stock|models?|model number|catalogues?|catalogs?|specs?|specifications?|jct \d|jcg \d|jcs \d|this product|which model)\b/.test(normalized)) {
    return makeReply(
      "I can’t access Jenga’s live catalogue while offline, so I can’t verify a product’s price, availability, model, or specifications. Reconnect to the service for current, source-backed information.",
    );
  }

  const found = conceptsInQuery(query);
  const isComparison = /\b(compare|comparison|difference|differences|versus|vs)\b/.test(normalized)
    || /\bdiffer(?:ent|s)? between\b/.test(normalized);
  if (isComparison && found.length >= 2) {
    return makeReply(
      `${firstSentence(found[0])} ${firstSentence(found[1])} In short: ${comparisonSummary(found[0], found[1])} Want me to compare them for a particular general use case?`,
    );
  }

  if (found.length > 0) {
    const concept = found[0];
    if (/\b(how|work|works|working|operate|operates)\b/.test(normalized)) {
      return makeReply(`${concept.mechanism} ${concept.analogy} This is general background, not instructions for a specific installation.`);
    }
    if (
      /\b(purpose|role|used for|use case|what .* for)\b/.test(normalized)
      || (/\b(use|why|for)\b/.test(normalized) && !/\bwhat is\b/.test(normalized))
    ) {
      return makeReply(`${concept.purpose} ${concept.analogy} The right application depends on the full system design.`);
    }
    return makeReply(
      `${concept.definition} ${concept.purpose} ${concept.analogy} Want to know how it works, what it is used for, or how it differs from another concept?`,
    );
  }

  return makeReply(
    "I don’t have enough offline context to answer that reliably. I can explain a general electrical concept or compare two terms—try asking “How does an inverter work?” or “What’s the difference between power and energy?” For a Jenga product, manual, price, or fault, reconnect so I can use current sources.",
  );
}

function firstSentence(concept: OfflineConcept): string {
  return `${concept.name}: ${concept.definition}`;
}
