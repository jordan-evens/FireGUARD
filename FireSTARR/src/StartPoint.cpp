// Copyright (C) 2020  Queen's Printer for Ontario
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// 
// Last Updated 2020-04-07 <Evens, Jordan (MNRF)>

#include "stdafx.h"
#include "StartPoint.h"
#include "Settings.h"
#include "Util.h"
namespace firestarr
{
namespace topo
{
template <typename T>
static T fix_range(T value, T min_value, T max_value) noexcept
{
  while (value < min_value)
  {
    value += max_value;
  }
  while (value >= max_value)
  {
    value -= max_value;
  }
  return value;
}
template <typename T>
static T fix_degrees(T value) noexcept
{
  return fix_range(value, 0.0, 360.0);
}
template <typename T>
static T fix_hours(T value) noexcept
{
  return fix_range(value, 0.0, 24.0);
}
static double sunrise_sunset(const int jd,
                             const double latitude,
                             const double longitude,
                             const bool for_sunrise) noexcept
{
  static const auto Zenith = util::to_radians(96);
  static const auto LocalOffset = -5;
  const auto t_hour = for_sunrise ? 6 : 18;
  // http://edwilliams.org/sunrise_sunset_algorithm.htm
  const auto lng_hour = longitude / 15;
  const auto t = jd + (t_hour - lng_hour) / 24;
  const auto m = 0.9856 * t - 3.289;
  const auto l = fix_degrees(
    m + 1.916 * sin(util::to_radians(m)) + 0.020 * sin(
      util::to_radians(2 * m)) + 282.634);
  auto ra = fix_degrees(util::to_degrees(atan(0.91764 * tan(util::to_radians(l)))));
  const auto l_quadrant = floor(l / 90) * 90;
  const auto ra_quadrant = floor(ra / 90) * 90;
  ra += l_quadrant - ra_quadrant;
  ra /= 15;
  const auto sin_dec = 0.39782 * sin(util::to_radians(l));
  const auto cos_dec = cos(asin(sin_dec));
  const auto cos_h = (cos(Zenith) - sin_dec * sin(util::to_radians(latitude))) / (cos_dec
    *
    cos(util::to_radians(latitude)));
  if (cos_h > 1)
  {
    // sun never rises
    return for_sunrise ? -1 : 25;
  }
  if (cos_h < -1)
  {
    // sun never sets
    return for_sunrise ? 25 : -1;
  }
  auto h = util::to_degrees(acos(cos_h));
  if (for_sunrise)
  {
    h = 360 - h;
  }
  h /= 15;
  const auto mean_t = h + ra - 0.06571 * t - 6.622;
  const auto ut = mean_t - lng_hour;
  return fix_hours(ut + LocalOffset);
}
static double sunrise(const int jd,
                      const double latitude,
                      const double longitude) noexcept
{
  return sunrise_sunset(jd, latitude, longitude, true);
}
static double sunset(const int jd, const double latitude, const double longitude) noexcept
{
  return sunrise_sunset(jd, latitude, longitude, false);
}
static array<tuple<double, double>, MAX_DAYS> make_days(
  const double latitude,
  const double longitude) noexcept
{
  array<tuple<double, double>, MAX_DAYS> days{};
  array<double, MAX_DAYS> day_length_hours{};
  for (size_t i = 0; i < day_length_hours.size(); ++i)
  {
    days[i] = make_tuple(
      fix_hours(
        sunrise(static_cast<int>(i), latitude, longitude) + sim::Settings::
        offsetSunrise()),
      fix_hours(
        sunset(static_cast<int>(i),
               latitude,
               longitude) - sim::Settings::offsetSunset()));
    day_length_hours[i] = get<1>(days[i]) - get<0>(days[i]);
  }
  return days;
}
StartPoint::StartPoint(const double latitude, const double longitude) noexcept
  : Point(latitude, longitude), days_(make_days(latitude, longitude))
{
}
#pragma warning (push)
#pragma warning (disable: 26456)
StartPoint& StartPoint::operator=(StartPoint&& rhs) noexcept
{
  if (this != &rhs)
  {
    Point::operator=(rhs);
    for (size_t i = 0; i < days_.size(); ++i)
    {
      days_[i] = rhs.days_[i];
    }
  }
  return *this;
}
#pragma warning (pop)
}
}
