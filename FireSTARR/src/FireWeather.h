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

#pragma once
#include <map>
#include <set>
#include <vector>
#include "FuelLookup.h"
#include "FWI.h"
#ifdef _DEBUG
#include "Log.h"
#endif
namespace firestarr
{
namespace wx
{
// use an array instead of a map since number of values is so small and access should be faster
using SurvivalMap = array<vector<float>, NUMBER_OF_FUELS>;
/**
 * \brief A stream of weather that gets used by a Scenario every Iteration.
 */
class FireWeather
{
public:
  /**
   * \brief Destructor
   */
  virtual ~FireWeather();
  /**
   * \brief Constructor
   * \param used_fuels set of FuelTypes that are used in the simulation
   * \param data map of Day to FwiWeather to use for weather stream
   */
  FireWeather(const set<const fuel::FuelType*>& used_fuels,
              const map<Day, FwiWeather>& data);
  /**
   * \brief Move constructor
   * \param rhs FireWeather to move from
   */
  FireWeather(FireWeather&& rhs) = default;
  FireWeather(const FireWeather& rhs) = delete;
  /**
   * \brief Move assignment
   * \param rhs FireWeather to move from
   * \return This, after assignment
   */
  FireWeather& operator=(FireWeather&& rhs) noexcept = default;
  FireWeather& operator=(const FireWeather& rhs) = delete;
  /**
   * \brief Get FwiWeather for given time
   * \param time Time to get weather for
   * \return FwiWeather for given time
   */
  [[nodiscard]] const FwiWeather* at(const double time) const
  {
#ifdef _DEBUG
				logging::check_fatal(time < 0 || time >= MAX_DAYS, "Invalid weather time %f", time);
#endif
    return weather_by_hour_by_day_->at(util::time_index(time, min_date_));
  }
  /**
   * \brief Probability of survival in given fuel at given time
   * \param time Time to get survival probability for
   * \param in_fuel FuelCodeSize of FuelType to use
   * \return Probability of survival in given fuel at given time
   */
  [[nodiscard]] double survivalProbability(const double time,
                                           const FuelCodeSize& in_fuel) const
  {
    return survival_probability_->at(in_fuel).at(util::time_index(time, min_date_));
  }
  /**
   * \brief Minimum date present in FireWeather
   * \return Minimum date present in FireWeather
   */
  [[nodiscard]] constexpr Day minDate() const { return min_date_; }
  /**
   * \brief Maximum date present in FireWeather
   * \return Maximum date present in FireWeather
   */
  [[nodiscard]] constexpr Day maxDate() const { return max_date_; }
  /**
   * \brief Weighted Danger Severity Rating for the stream
   * \return Weighted Danger Severity Rating for the stream
   */
  [[nodiscard]] constexpr size_t weightedDsr() const noexcept { return weighted_dsr_; }
protected:
  /**
   * \brief Constructor
   * \param used_fuels set of FuelTypes that are used in the simulation
   * \param min_date Minimum date present in stream
   * \param max_date Maximum date present in stream
   * \param weather_by_hour_by_day FwiWeather by hour by Day
   */
  FireWeather(const set<const fuel::FuelType*>& used_fuels,
              Day min_date,
              Day max_date,
              vector<const FwiWeather*>* weather_by_hour_by_day);
private:
  /**
   * \brief FwiWeather by hour by Day
   */
  const vector<const FwiWeather*>* weather_by_hour_by_day_;
  /**
   * \brief Probability of survival for fuels fuel at each time
   */
  const SurvivalMap* survival_probability_;
  /**
   * \brief Minimum date present in stream
   */
  Day min_date_;
#pragma warning (push)
#pragma warning (disable: 4820)
  /**
   * \brief Maximum date present in stream
   */
  Day max_date_;
  /**
   * \brief Weighted Danger Severity Rating for the stream
   */
  size_t weighted_dsr_;
};
#pragma warning (pop)
/**
 * \brief Equality operator
 * \param lhs First FireWeather
 * \param rhs Second FireWeather
 * \return Whether or not the two FireWeathers are equal
 */
[[nodiscard]] constexpr bool operator==(const FireWeather& lhs, const FireWeather& rhs)
{
  if (!(lhs.maxDate() == rhs.maxDate() && lhs.minDate() == rhs.minDate()))
  {
    return false;
  }
  // FIX: why is this a warning?
#pragma warning (push)
#pragma warning (disable: 4365)
  for (Day day = lhs.minDate() + static_cast<Day>(1); day <= lhs.maxDate(); ++day)
#pragma warning (pop)
  {
    for (auto hour = 0; hour < DAY_HOURS; ++hour)
    {
      const auto time = static_cast<double>(day) + hour / 24.0;
      if (lhs.at(time) != rhs.at(time))
      {
        return false;
      }
    }
  }
  return true;
}
/**
 * \brief Inequality operator
 * \param lhs First FireWeather
 * \param rhs Second FireWeather
 * \return Whether or not they are not equivalent
 */
[[nodiscard]] constexpr bool operator!=(const FireWeather& lhs, const FireWeather& rhs)
{
  return !(lhs == rhs);
}
}
}
