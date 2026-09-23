-- word_freq: count words in generated text and rank them. The four
-- Benchmarks Game scripts are numeric. This one is the kind of Lua people
-- write for real work: string scanning, string-keyed tables, sorting with
-- a comparator and building output with string.format.
--
-- N is the number of lines of text (each line has 4 to 15 words). The work
-- grows linearly with N.
--
-- The text comes from a fixed-seed LCG, so every run sees the same words.
-- The words are string keys, and Lua places them in its hash tables by a
-- seed that the build fixes (luai_makeseed, see p2p.patch). So the table
-- layout, and the branches that walk it, are the same on every run too.
--
-- The check: the per-word counts must add up to the number of words the
-- generator wrote, and the ranked list must be in order. The exact ranking
-- is in expected.json.

local words = {
  "the", "of", "and", "to", "in", "is", "that", "it", "was", "for",
  "on", "are", "as", "with", "his", "they", "at", "be", "this", "have",
  "from", "or", "one", "had", "by", "word", "but", "not", "what", "all",
  "were", "we", "when", "your", "can", "said", "there", "use", "an",
  "each", "which", "she", "do", "how", "their", "if", "will", "up",
  "other", "about", "out", "many", "then", "them", "these", "so", "some",
  "her", "would", "make", "like", "him", "into", "time", "has", "look",
  "two", "more", "write", "go", "see", "number", "no", "way", "could",
  "people", "my", "than", "first", "water", "been", "call", "who", "oil",
  "its", "now", "find", "long", "down", "day", "did", "get", "come",
  "made", "may", "part", "branch", "predictor", "register", "value",
  "history", "table", "counter", "pipeline", "cache", "memory",
  "instruction", "cycle", "statistical", "corrector", "confidence",
  "threshold", "loop", "global", "local", "path", "signature", "entry",
  "tag", "index", "update", "commit", "fetch", "decode", "retire",
  "squash", "bias", "ahead",
}
local nwords = #words

-- 31-bit LCG (the ANSI C rand() constants). Lua integers are 64-bit, so
-- the product cannot overflow before the mask.
local state = 12345
local function rand()
  state = (state * 1103515245 + 12345) & 0x7fffffff
  return state >> 8
end

-- Build the text as lines. A skewed pick (the smaller of two draws) makes
-- early words common and late words rare. Some words get a capital letter
-- or a trailing comma, so the counting step has to normalise them.
local lines = {}
local generated = 0
for l = 1, N do
  local len = 4 + rand() % 12
  local parts = {}
  for w = 1, len do
    local a, b = rand() % nwords, rand() % nwords
    local word = words[(a < b and a or b) + 1]
    local r = rand() % 16
    if w == 1 or r == 0 then
      word = word:sub(1, 1):upper() .. word:sub(2)
    end
    if r == 1 and w < len then
      word = word .. ","
    end
    parts[w] = word
  end
  generated = generated + len
  lines[l] = table.concat(parts, " ") .. "."
end

-- Count words, case-folded, with punctuation stripped by the pattern.
local counts = {}
local total = 0
for l = 1, N do
  for word in lines[l]:gmatch("%a+") do
    word = word:lower()
    counts[word] = (counts[word] or 0) + 1
    total = total + 1
  end
end

-- Rank by count, then alphabetically, so ties have one order.
local ranked = {}
for word, c in pairs(counts) do
  ranked[#ranked + 1] = {word = word, count = c}
end
table.sort(ranked, function(x, y)
  if x.count ~= y.count then
    return x.count > y.count
  end
  return x.word < y.word
end)

local sorted = true
for i = 2, #ranked do
  local x, y = ranked[i - 1], ranked[i]
  if x.count < y.count or (x.count == y.count and x.word >= y.word) then
    sorted = false
  end
end

-- A position-weighted checksum over the whole ranking, so a change
-- anywhere in the order shows up in one printed number.
local checksum = 0
for i, e in ipairs(ranked) do
  for k = 1, #e.word do
    checksum = (checksum * 31 + e.word:byte(k) + i * e.count) % 1000000007
  end
end

print(string.format("lines %d words %d distinct %d", N, total, #ranked))
for i = 1, math.min(5, #ranked) do
  print(string.format("%-12s %d", ranked[i].word, ranked[i].count))
end
print(string.format("checksum %d", checksum))

return total == generated and sorted
