# Our statewide analysis of the difference in turnout between Black (w = 1) and
# non-Black (w = 0) registered voters in Georgia, at n1 = n0 = 300.
#
# To analyze the candidate's vote share theta = f(mu.1, mu.0) instead of the difference, change
# the two marked lines. Nothing else needs to change.

library(tidyverse)
set.seed(285)

ga = read.csv('data/ga_turnout_2024_county_race.csv')
black = ga$race == 'Black'

m1 = sum(ga$registered[black]);  v1 = sum(ga$voted[black])
m0 = sum(ga$registered[!black]); v0 = sum(ga$voted[!black])
m  = m1 + m0

mu.1 = v1/m1   # turnout among Black registrants
mu.0 = v0/m0   # turnout among non-Black registrants
a    = m1/m    # Black share of the roll
b    = m0/m    # non-Black share of the roll
q.1  = .90     # the candidate's share among Black voters
q.0  = .45     # the candidate's share among non-Black voters

n1 = 300
n0 = 300

sigma.sq = function(mu)      { mu*(1-mu) }
fpc      = function(m.w,n.w) { (m.w-n.w)/(m.w-1) }

V1 = sigma.sq(mu.1)/n1 * fpc(m1,n1)
V0 = sigma.sq(mu.0)/n0 * fpc(m0,n0)

theta    = function(mu.1, mu.0)     { mu.1 - mu.0 }   # <- the estimation target
variance = function(V1, V0, mu.1, mu.0) { V1 + V0 }   # <- and its variance

one.study = function() {
  muhat.1 = rhyper(1, m=v1, n=m1-v1, k=n1)/n1
  muhat.0 = rhyper(1, m=v0, n=m0-v0, k=n0)/n0
  # A difference has no denominator, so this guard does nothing until you switch to
  # the ratio. There it keeps the draws with a*muhat.1 + b*muhat.0 = 0 countable instead of silent.
  data.frame(thetahat = if (a*muhat.1 + b*muhat.0 > 0) theta(muhat.1,muhat.0) else NA)
}
studies = 1:2000 |> map(\(.) one.study()) |> bind_rows()

c(target  = theta(mu.1, mu.0),
  se      = sqrt(variance(V1, V0, mu.1, mu.0)),
  sim.mean = mean(studies$thetahat, na.rm=TRUE),
  sim.sd   = sd(studies$thetahat,   na.rm=TRUE),
  zero.denominators = sum(is.na(studies$thetahat)))
