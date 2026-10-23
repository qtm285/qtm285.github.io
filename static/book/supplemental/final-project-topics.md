# topics-doc

# QTM 285 — Final Project Topics

Six options. You'll work in pairs or threes on a small set of related papers: one study whose data you dig into, and one or more that complicate it. Every topic below has data we have checked and can give you.

You are not expected to find errors. Establishing that a study's methods were sound is as good an outcome as finding a problem with them.

---

## 1. Does anti-LGBTQ political messaging win elections?

**Papers.** Haas, Bogatyrev, Abou-Chadi, Klüver & Stoetzer, *The Electoral Effects of State-Sponsored Anti-LGBTQ Measures*. Ayoub, Page & Whitt, *Anti-LGBTIQ Rhetoric and Electoral Outcomes under the Shadow of War* (2025).

**Summary.** Between 2019 and 2021, 109 Polish local and regional governments passed resolutions against "LGBT ideology." Haas and colleagues ask whether this moved election results, using municipal returns from six parliamentary elections. Ayoub and colleagues ask a related question with a randomized survey experiment on 1,000 Polish voters during the war in Ukraine. You get both datasets and the authors' code.

**Challenges.** The survey experiment is a clean difference in proportions — four randomly assigned groups, a yes-or-no outcome — and a good place to start. The observational study is harder: resolutions were passed at three different levels of government, so a single county resolution treats every municipality inside it at once. Hundreds of municipalities, far fewer independent decisions. What does that do to the uncertainty? There are also 87 councils that debated the same resolution and voted it down, which may be a better comparison group than untreated municipalities generally.

## 2. What do résumé experiments tell us about discrimination?

**Papers.** Bertrand & Mullainathan, *Are Emily and Greg More Employable Than Lakisha and Jamal?* (2004). Kohler-Hausmann, on what such experiments measure.

**Summary.** The researchers sent nearly 5,000 fictitious résumés to real employers, varying only the name, and recorded callbacks. The randomization is clean and the gap is large. The second reading asks what you have actually manipulated when you change a name, and whether a precisely estimated difference supports the conclusion usually drawn from it.

**Challenges.** Callbacks are uncommon, which drives how large a study like this has to be — a power calculation worth doing. Résumés went to employers in batches, so think about what the unit of assignment really is. And the interpretive problem is genuine: no additional data settles it, which makes it a different kind of difficulty from the rest of this list.

## 3. What does hormone therapy do for women's health?

**Papers.** The Women's Health Initiative randomized trial. The Study of Women's Health Across the Nation (SWAN).

**Summary.** Observational research long suggested hormone therapy protected women's health; a large randomized trial then reported harms and practice changed abruptly. Why did two bodies of evidence disagree? We will give you data from SWAN, which followed 3,302 women through menopause. None were using hormone therapy at enrolment and 527 started later, so every woman has symptoms measured before any treatment.

**Challenges.** Comparing those who started against those who never did is easy; the comparison is also not a treatment effect, because women who start are not like women who don't. Compare the groups on everything measured *before* treatment and see how far apart they are. Then ask what survives when you compare like with like. Two variables you would want — education and the clinical site — are not in the public release, so part of the work is saying precisely what you cannot rule out.

## 4. Can small incentives improve public health?

**Papers.** Banerjee, Duflo, Glennerster & Kothari, *Improving Immunisation Coverage in Rural India* (2010).

**Summary.** Facing very low immunization rates in rural Rajasthan, the researchers randomly assigned 134 villages to reliable monthly immunization camps, camps plus a small food incentive, or nothing. The data is fully public: 74 control villages, 30 with camps, 30 with incentives, and records for 5,565 children, each linked to its village.

**Challenges.** Full immunization is a yes-or-no outcome, so the headline is a difference in proportions. But villages were assigned, not children, and children in a village are not independent — thousands of children, 134 independent assignments. That gap is the centre of this project, for both uncertainty and study size. You will also have to decide what "fully immunized" means; the authors' code offers several definitions and age ranges, and the answer moves.

## 5. Are healthcare algorithms measuring the right thing?

**Papers.** Obermeyer, Powers, Vogeli & Mullainathan, *Dissecting Racial Bias in an Algorithm Used to Manage the Health of Populations* (2019).

**Summary.** A widely deployed algorithm decided who received extra medical care by predicting their future cost, with cost standing in for how sick they were. If two equally sick people generate different spending, the algorithm ranks them differently while believing it ranks them by need. The public data covers 48,784 patient-years: the algorithm's risk score, spending, a count of active chronic illnesses, demographics and lab values.

**Challenges.** Take patients the algorithm scored identically and ask whether they are equally sick — a comparison of averages within groups is enough to see the whole phenomenon. Then press on it: how much depends on how you measure "sick"? The data is synthetic, built to imitate confidential records, so think about what that licenses you to claim.

## 6. Do student evaluations measure good teaching?

**Papers.** Carrell & West, *Does Professor Quality Matter?* (2010). Braga, Paccagnella & Pellizzari, *Evaluating Students' Evaluations of Professors* (2014).

**Summary.** At the US Air Force Academy students are randomly assigned to instructors and then all sit the same follow-on courses — so you can ask whether instructors who produce the best immediate grades and evaluations also produce students who do better later. The authors report they do not. You cannot have their data: it belongs to the Air Force Academy and requires institutional permission. A great deal of published research rests on data its readers cannot see, so this topic asks what you can legitimately establish about a study you cannot rerun.

**Challenges.** You get their published tables, their complete analysis code, and the log of everything their program printed — including summary statistics for every variable. From that, build a simulated version of their study: same number of instructors, same spread of class sizes, same variation in student ability. Run their procedure on your simulation, where you know the truth, and ask whether a study of that size could reliably detect an effect as small as the one reported. Note that instructors taught between 1 and 43 sections, so a few carry much more of the comparison than the rest.

---

**A thread across the six.** Three of these studies rest on data you cannot freely see, and the researchers handled it three different ways: Carrell and West released code and no data, Obermeyer's team released synthetic data imitating the real records, and the hormone trial keeps its records behind an application. Groups on different topics will meet the same wall from different sides, and should compare notes.
