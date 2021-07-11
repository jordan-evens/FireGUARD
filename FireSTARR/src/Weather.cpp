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
#include "Weather.h"
#include "Log.h"
#include "TimeUtil.h"
namespace firestarr
{
namespace wx
{
const Temperature Temperature::Zero = Temperature(0);
const RelativeHumidity RelativeHumidity::Zero = RelativeHumidity(0);
const Direction Direction::Zero = Direction(0, false);
const Speed Speed::Zero = Speed(0);
const Wind Wind::Zero = Wind(Direction(0, false), Speed(0));
const AccumulatedPrecipitation AccumulatedPrecipitation::Zero =
  AccumulatedPrecipitation(0);
}
}
