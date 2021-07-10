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
#include "Settings.h"

namespace firestarr
{
namespace sim
{
/**
 * \brief The position within a Cell that a spreading point has.
 */
struct InnerPos
{
  /**
   * \brief X coordinate
   */
  double x;
  /**
   * \brief Y coordinate
   */
  double y;
  /**
   * \brief Constructor
   * \param x X coordinate
   * \param y Y coordinate
   */
  InnerPos(const double x, const double y) noexcept
    : x(x), y(y)
  {
  }
  /**
   * \brief Less than operator
   * \param rhs InnerPos to compare to
   * \return Whether or not this is less than the other
   */
  bool operator<(const InnerPos& rhs) const noexcept
  {
    if (x == rhs.x)
    {
      return y < rhs.y;
    }
    return x < rhs.x;
  }
  /**
   * \brief Equality operator
   * \param rhs InnerPos to compare to
   * \return Whether or not this is equivalent to the other
   */
  bool operator==(const InnerPos& rhs) const noexcept
  {
    return abs(x - rhs.x) < COMPARE_LIMIT && abs(y - rhs.y) < COMPARE_LIMIT;
  }
};
}
}
