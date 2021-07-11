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
#include "Duff.h"
#include "FireSpread.h"
#include "LookupTable.h"
#include "StandardFuel.h"
#ifndef NDEBUG
#include "Log.h"
#endif
namespace firestarr
{
namespace fuel
{
/**
 * \brief Calculate if green-up has occurred
 * \param nd Difference between date and the date of minimum foliar moisture content
 * \return Whether or no green-up has occurred
 */
[[nodiscard]] constexpr bool calculate_is_green(const int nd)
{
  return nd >= 30;
}
/**
 * \brief Use intersection of parabola with y = 120.0 line as point where grass greening starts happening.
 */
static constexpr int START_GREENING = -43;
[[nodiscard]] constexpr int calculate_grass_curing(const int nd)
{
  return (nd < START_GREENING)
           ?  // we're before foliar moisture dip has started
           100
           : (nd >= 50)
           ? 0  // foliar moisture is at 120.0, so grass should be totally uncured
           // HACK: invent a formula that has 50% curing at the bottom of the foliar
           // moisture dip foliar moisture above ranges between 120 and 85, with 85
           // being at the point where we want 50% cured Curing:
           // -43 => 100, 0 => 50, 50 => 0 least-squares best fit:
           : static_cast<int>(52.5042 - 1.07324 * nd);
}
[[nodiscard]] static double
calculate_surface_fuel_consumption_mixed_or_c2(const double bui) noexcept
{
  return 5.0 * (1.0 - exp(-0.0115 * bui));
}
static const util::LookupTable<&calculate_surface_fuel_consumption_mixed_or_c2>
SURFACE_FUEL_CONSUMPTION_MIXED_OR_C2{};
[[nodiscard]] static double
calculate_surface_fuel_consumption_d1(const double bui) noexcept
{
  return 1.5 * (1.0 - exp(-0.0183 * bui));
}
static util::LookupTable<&calculate_surface_fuel_consumption_d1>
SURFACE_FUEL_CONSUMPTION_D1{};
/**
 * \brief A StandardFuel that is not made of multiple fuels.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam Cbh Crown base height (m) [ST-X-3 table 8]
 * \tparam Cfl Crown fuel load (kg/m^2) [ST-X-3 table 8]
 * \tparam BulkDensity Crown bulk density * 1000 [Anderson table 1]
 * \tparam InorganicPercent Inorganic percent of Duff layer (%) [Anderson table 1]
 * \tparam DuffDepth Depth of Duff layer (cm * 10) [Anderson table 1]
 */
template <int A, int B, int C, int Bui0, int Cbh, int Cfl, int BulkDensity, int
          InorganicPercent, int DuffDepth>
class FuelNonMixed
  : public StandardFuel<A, B, C, Bui0, Cbh, Cfl, BulkDensity, InorganicPercent, DuffDepth>
{
public:
  FuelNonMixed() = delete;
  ~FuelNonMixed() = default;
  FuelNonMixed(const FuelNonMixed& rhs) noexcept = delete;
  FuelNonMixed(FuelNonMixed&& rhs) noexcept = delete;
  FuelNonMixed& operator=(const FuelNonMixed& rhs) noexcept = delete;
  FuelNonMixed& operator=(FuelNonMixed&& rhs) noexcept = delete;
protected:
  using StandardFuel<A, B, C, Bui0, Cbh, Cfl, BulkDensity, InorganicPercent, DuffDepth>::
    StandardFuel;
  /**
   * \brief ISI with slope influence and zero wind (ISF) [ST-X-3 eq 41]
   * \param spread SpreadInfo to use in calculations
   * \param isi Initial Spread Index
   * \return ISI with slope influence and zero wind (ISF) [ST-X-3 eq 41]
   */
  [[nodiscard]] double calculateIsf(const SpreadInfo& spread,
                                    const double isi) const noexcept override
  {
    return this->limitIsf(1.0,
                          calculateRos(spread.nd(),
                                       *spread.weather(),
                                       isi) * spread.slopeFactor());
  }
  /**
   * \brief Initial rate of spread (m/min) [ST-X-3 eq 26]
   * \param isi Initial Spread Index
   * \return Initial rate of spread (m/min) [ST-X-3 eq 26]
   */
  [[nodiscard]] double calculateRos(const int,
                                    const wx::FwiWeather&,
                                    const double isi) const noexcept override
  {
    return this->rosBasic(isi);
  }
};
/**
 * \brief A conifer fuel type.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam Cbh Crown base height (m) [ST-X-3 table 8]
 * \tparam Cfl Crown fuel load (kg/m^2) [ST-X-3 table 8]
 * \tparam BulkDensity Crown bulk density * 1000 [Anderson table 1]
 * \tparam InorganicPercent Inorganic percent of Duff layer (%) [Anderson table 1]
 * \tparam DuffDepth Depth of Duff layer (cm * 10) [Anderson table 1]
 */
template <int A, int B, int C, int Bui0, int Cbh, int Cfl, int BulkDensity, int
          InorganicPercent, int DuffDepth>
class FuelConifer
  : public FuelNonMixed<A, B, C, Bui0, Cbh, Cfl, BulkDensity, InorganicPercent, DuffDepth>
{
public:
  FuelConifer() = delete;
  ~FuelConifer() = default;
  FuelConifer(const FuelConifer& rhs) noexcept = delete;
  FuelConifer(FuelConifer&& rhs) noexcept = delete;
  FuelConifer& operator=(const FuelConifer& rhs) noexcept = delete;
  FuelConifer& operator=(FuelConifer&& rhs) noexcept = delete;
protected:
  /**
   * \brief A conifer FBP fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param log_q Log value of q [ST-X-3 table 7]
   * \param duff_ffmc Type of duff near the surface
   * \param duff_dmc Type of duff deeper underground
   */
  constexpr FuelConifer(const FuelCodeSize& code,
                        const char* name,
                        const LogValue log_q,
                        const Duff* duff_ffmc,
                        const Duff* duff_dmc)
    : FuelNonMixed<A, B, C, Bui0, Cbh, Cfl, BulkDensity, InorganicPercent, DuffDepth>(code,
                                                                                      name,
                                                                                      true,
                                                                                      log_q,
                                                                                      duff_ffmc,
                                                                                      duff_dmc)
  {
  }
  /**
   * \brief A conifer FBP fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param log_q Log value of q [ST-X-3 table 7]
   * \param duff Type of duff near the surface and deeper underground
   */
  constexpr FuelConifer(const FuelCodeSize& code,
                        const char* name,
                        const LogValue log_q,
                        const Duff* duff)
    : FuelConifer(code,
                  name,
                  log_q,
                  duff,
                  duff)
  {
  }
};
/**
 * \brief Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 11]
 * \param bui Build-up Index
 * \return Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 11]
 */
[[nodiscard]] static double calculate_surface_fuel_consumption_jackpine(
  const double bui) noexcept
{
  return 5.0 * pow(1.0 - exp(-0.0164 * bui), 2.24);
}
/**
 * \brief Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 11]
 * \return Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 11]
 */
static util::LookupTable<&calculate_surface_fuel_consumption_jackpine>
SURFACE_FUEL_CONSUMPTION_JACKPINE{};
/**
 * \brief A fuel with jackpine as base fuel type.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam Cbh Crown base height (m) [ST-X-3 table 8]
 * \tparam Cfl Crown fuel load (kg/m^2) [ST-X-3 table 8]
 * \tparam BulkDensity Crown bulk density * 1000 [Anderson table 1]
 * \tparam DuffDepth Depth of Duff layer (cm * 10) [Anderson table 1]
 */
template <int A, int B, int C, int Bui0, int Cbh, int Cfl, int BulkDensity, int DuffDepth>
class FuelJackpine
  : public FuelConifer<A, B, C, Bui0, Cbh, Cfl, BulkDensity, 15, DuffDepth>
{
public:
  FuelJackpine() = delete;
  ~FuelJackpine() = default;
  FuelJackpine(const FuelJackpine& rhs) noexcept = delete;
  FuelJackpine(FuelJackpine&& rhs) noexcept = delete;
  FuelJackpine& operator=(const FuelJackpine& rhs) noexcept = delete;
  FuelJackpine& operator=(FuelJackpine&& rhs) noexcept = delete;
  using FuelConifer<A, B, C, Bui0, Cbh, Cfl, BulkDensity, 15, DuffDepth>::FuelConifer;
  /**
   * \brief Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 11]
   * \param spread SpreadInfo to use
   * \return Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 11]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override
  {
    return SURFACE_FUEL_CONSUMPTION_JACKPINE(spread.bui().asDouble());
  }
};
/**
 * \brief Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 12]
 * \param bui Build-up Index
 * \return Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 12]
 */
[[nodiscard]] static double
calculate_surface_fuel_consumption_pine(const double bui) noexcept
{
  return 5.0 * pow(1.0 - exp(-0.0149 * bui), 2.48);
}
/**
 * \brief Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 12]
 * \param bui Build-up Index
 * \return Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 12]
 */
static util::LookupTable<&calculate_surface_fuel_consumption_pine>
SURFACE_FUEL_CONSUMPTION_PINE
  {};
/**
 * \brief A fuel with pine as the base fuel type.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam Cbh Crown base height (m) [ST-X-3 table 8]
 * \tparam Cfl Crown fuel load (kg/m^2) [ST-X-3 table 8]
 * \tparam BulkDensity Crown bulk density * 1000 [Anderson table 1]
 * \tparam DuffDepth Depth of Duff layer (cm * 10) [Anderson table 1]
 */
template <int A, int B, int C, int Bui0, int Cbh, int Cfl, int BulkDensity, int DuffDepth>
class FuelPine : public FuelConifer<A, B, C, Bui0, Cbh, Cfl, BulkDensity, 15, DuffDepth>
{
public:
  FuelPine() = delete;
  ~FuelPine() = default;
  FuelPine(const FuelPine& rhs) noexcept = delete;
  FuelPine(FuelPine&& rhs) noexcept = delete;
  FuelPine& operator=(const FuelPine& rhs) noexcept = delete;
  FuelPine& operator=(FuelPine&& rhs) noexcept = delete;
  using FuelConifer<A, B, C, Bui0, Cbh, Cfl, BulkDensity, 15, DuffDepth>::FuelConifer;
  /**
   * \brief Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 12]
   * \param spread SpreadInfo to use
   * \return Surface fuel consumption (SFC) (kg/m^2) [ST-X-3 eq 12]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override
  {
    return SURFACE_FUEL_CONSUMPTION_PINE(spread.bui().asDouble());
  }
};
namespace fbp
{
/**
 * \brief FBP fuel type D-1.
 */
class FuelD1 : public FuelNonMixed<30, 232, 160, 32, 0, 0, 61, 59, 24>
{
public:
  FuelD1() = delete;
  ~FuelD1() = default;
  FuelD1(const FuelD1& rhs) noexcept = delete;
  FuelD1(FuelD1&& rhs) noexcept = delete;
  FuelD1& operator=(const FuelD1& rhs) noexcept = delete;
  FuelD1& operator=(FuelD1&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type D-1
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelD1(const FuelCodeSize& code) noexcept
    : FuelNonMixed(code,
                   "D-1",
                   false,
                   data::LOG_0_9,
                   &Duff::Peat)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 25]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 25]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override
  {
    return SURFACE_FUEL_CONSUMPTION_D1(spread.bui().asDouble());
  }
  /**
   * \brief Calculate ISI with slope influence and zero wind (ISF) for D-1 [ST-X-3 eq 41]
   * \param spread SpreadInfo to use
   * \param ros_multiplier Rate of spread multiplier [ST-X-3 eq 27/28, GLC-X-10 eq 29/30]
   * \param isi Initial Spread Index
   * \return ISI with slope influence and zero wind (ISF) for D-1 [ST-X-3 eq 41]
   */
  [[nodiscard]] double isfD1(const SpreadInfo& spread,
                             double ros_multiplier,
                             double isi) const noexcept;
};
}
/**
 * \brief A mixedwood fuel type.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam RosMultiplier Rate of spread multiplier * 10 [ST-X-3 eq 27/28, GLC-X-10 eq 29/30]
 * \tparam PercentMixed Percent conifer or dead fir
 * \tparam BulkDensity Crown bulk density * 1000 [Anderson table 1]
 * \tparam InorganicPercent Inorganic percent of Duff layer (%) [Anderson table 1]
 * \tparam DuffDepth Depth of Duff layer (cm * 10) [Anderson table 1]
 */
template <int A, int B, int C, int Bui0, int RosMultiplier, int PercentMixed, int
          BulkDensity, int InorganicPercent, int DuffDepth>
class FuelMixed
  : public StandardFuel<A, B, C, Bui0, 6, 80, BulkDensity, InorganicPercent, DuffDepth>
{
public:
  FuelMixed() = delete;
  ~FuelMixed() = default;
  FuelMixed(const FuelMixed& rhs) noexcept = delete;
  FuelMixed(FuelMixed&& rhs) noexcept = delete;
  FuelMixed& operator=(const FuelMixed& rhs) noexcept = delete;
  FuelMixed& operator=(FuelMixed&& rhs) noexcept = delete;
  /**
   * \brief A mixed FBP fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param log_q Log value of q [ST-X-3 table 7]
   */
  constexpr FuelMixed(const FuelCodeSize& code,
                      const char* name,
                      const LogValue log_q)
    : StandardFuel<A, B, C, Bui0, 6, 80, BulkDensity, InorganicPercent, DuffDepth>(code,
                                                                                   name,
																				   true,
																				   log_q,
																				   &Duff::Peat,
																				   &Duff::Peat)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 10]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 10]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override
  {
    return SURFACE_FUEL_CONSUMPTION_MIXED_OR_C2(spread.bui().asDouble());
  }
  /**
   * \brief Crown Fuel Consumption (CFC) (kg/m^2) [ST-X-3 eq 66, pg 38]
   * \param cfb Crown Fraction Burned (CFB) [ST-X-3 eq 58]
   * \return Crown Fuel Consumption (CFC) (kg/m^2) [ST-X-3 eq 66, pg 38]
   */
  [[nodiscard]] double crownConsumption(const double cfb) const noexcept override
  {
    return ratioConifer() * StandardFuel<
        A, B, C, Bui0, 6, 80, BulkDensity, InorganicPercent, DuffDepth>::
      crownConsumption(cfb);
  }
  /**
   * \brief Calculate rate of spread (m/min) [ST-X-3 27/28, GLC-X-10 29/31]
   * \param isi Initial Spread Index
   * \return Calculate rate of spread (m/min) [ST-X-3 27/28, GLC-X-10 29/31]
   */
  [[nodiscard]] double calculateRos(const int,
                                    const wx::FwiWeather&,
                                    const double isi) const noexcept override
  {
    static const fbp::FuelD1 F{14};
    return ratioConifer() * this->rosBasic(isi) + rosMultiplier() * ratioDeciduous() * F.
      rosBasic(isi);
  }
  /**
   * \brief Calculate ISI with slope influence and zero wind (ISF) [ST-X-3 eq 42]
   * \param spread SpreadInfo to use
   * \param isi Initial Spread Index
   * \return ISI with slope influence and zero wind (ISF) [ST-X-3 eq 42]
   */
  [[nodiscard]] double calculateIsf(const SpreadInfo& spread,
                                    const double isi) const noexcept override
  {
    return ratioConifer() * this->limitIsf(1.0,
                                           spread.slopeFactor() * this->rosBasic(isi))
      + ratioDeciduous() * isfD1(spread, isi);
  }
  /**
   * \brief Percent Conifer (% / 100)
   * \return Percent Conifer (% / 100)
   */
  [[nodiscard]] static constexpr double ratioConifer() { return PercentMixed / 100.0; }
  /**
   * \brief Percent Deciduous (% / 100)
   * \return Percent Deciduous (% / 100)
   */
  [[nodiscard]] static constexpr double ratioDeciduous()
  {
    return 1.0 - (PercentMixed / 100.0);
  }
protected:
  /**
   * \brief Rate of spread multiplier [ST-X-3 eq 27/28, GLC-X-10 eq 29/30]
   * \return Rate of spread multiplier [ST-X-3 eq 27/28, GLC-X-10 eq 29/30]
   */
  [[nodiscard]] static constexpr double rosMultiplier() { return RosMultiplier / 10.0; }
  /**
   * \brief Calculate ISI with slope influence and zero wind (ISF) for D-1 [ST-X-3 eq 41]
   * \param spread SpreadInfo to use
   * \param isi Initial Spread Index
   * \return ISI with slope influence and zero wind (ISF) for D-1 [ST-X-3 eq 41]
   */
  [[nodiscard]] static double isfD1(const SpreadInfo& spread,
                                    const double isi) noexcept
  {
    static const fbp::FuelD1 F{14};
    return F.isfD1(spread, rosMultiplier(), isi);
  }
};
/**
 * \brief A fuel made of dead fir and D1.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam RosMultiplier Rate of spread multiplier * 10 [ST-X-3 eq 27/28, GLC-X-10 eq 29/30]
 * \tparam PercentDeadFir Percent dead fir in the stand.
 */
template <int A, int B, int C, int Bui0, int RosMultiplier, int PercentDeadFir>
class FuelMixedDead
  : public FuelMixed<A, B, C, Bui0, RosMultiplier, PercentDeadFir, 61, 15, 75>
{
public:
  FuelMixedDead() = delete;
  ~FuelMixedDead() = default;
  FuelMixedDead(const FuelMixedDead& rhs) noexcept = delete;
  FuelMixedDead(FuelMixedDead&& rhs) noexcept = delete;
  FuelMixedDead& operator=(const FuelMixedDead& rhs) noexcept = delete;
  FuelMixedDead& operator=(FuelMixedDead&& rhs) noexcept = delete;
  /**
   * \brief A mixed dead FBP fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param log_q Log value of q [ST-X-3 table 7]
   */
  constexpr FuelMixedDead(const FuelCodeSize& code,
                          const char* name,
                          const LogValue log_q)
    : FuelMixed<A, B, C, Bui0, RosMultiplier, PercentDeadFir, 61, 15, 75>(code,
                                                                          name,
																		  log_q)
  {
  }
};
/**
 * \brief A fuel composed of C2 and D1 mixed.
 * \tparam RosMultiplier Rate of spread multiplier * 10 [ST-X-3 eq 27/28, GLC-X-10 eq 29/30]
 * \tparam RatioMixed Percent conifer
 */
template <int RosMultiplier, int RatioMixed>
class FuelMixedWood
  : public FuelMixed<110, 282, 150, 50, RosMultiplier, RatioMixed, 108, 25, 50>
{
public:
  FuelMixedWood() = delete;
  ~FuelMixedWood() = default;
  FuelMixedWood(const FuelMixedWood& rhs) noexcept = delete;
  FuelMixedWood(FuelMixedWood&& rhs) noexcept = delete;
  FuelMixedWood& operator=(const FuelMixedWood& rhs) noexcept = delete;
  FuelMixedWood& operator=(FuelMixedWood&& rhs) noexcept = delete;
  /**
   * \brief A mixedwood FBP fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   */
  constexpr FuelMixedWood(const FuelCodeSize& code,
                          const char* name)
    : FuelMixed<110, 282, 150, 50, RosMultiplier, RatioMixed, 108, 25, 50>(code,
                                                                           name,
																		   data::LOG_0_8)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 17]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 17]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override
  {
    return this->ratioConifer() * FuelMixed<
        110, 282, 150, 50, RosMultiplier, RatioMixed, 108, 25, 50>::
      surfaceFuelConsumption(spread)
      + this->ratioDeciduous() * SURFACE_FUEL_CONSUMPTION_D1(spread.bui().asDouble());
  }
};
/**
 * \brief Length to Breadth ratio [ST-X-3 eq 80/81]
 */
[[nodiscard]] static double calculate_length_to_breadth_grass(const double ws) noexcept
{
  return ws < 1.0 ? 1.0 : (1.1 * pow(ws, 0.464));
}
/**
 * \brief Length to Breadth ratio [ST-X-3 eq 80/81]
 */
static util::LookupTable<calculate_length_to_breadth_grass> LENGTH_TO_BREADTH_GRASS{};
/**
 * \brief Base multiplier for rate of spread [GLC-X-10 eq 35a/35b]
 * \param curing Grass fuel curing rate (%)
 * \return Base multiplier for rate of spread [GLC-X-10 eq 35a/35b]
 */
[[nodiscard]] static double calculate_base_multiplier_curing(const double curing) noexcept
{
  return (curing >= 58.8)
           ? (0.176 + 0.02 * (curing - 58.8))
           : (0.005 * expm1(0.061 * curing));
}
/**
 * \brief Base multiplier for rate of spread [GLC-X-10 eq 35a/35b]
 * \return Base multiplier for rate of spread [GLC-X-10 eq 35a/35b]
 */
static util::LookupTable<&calculate_base_multiplier_curing> BASE_MULTIPLIER_CURING{};
/**
 * \brief A grass fuel type.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 */
template <int A, int B, int C>
class FuelGrass
  : public StandardFuel<A, B, C, 1, 0, 0, 0, 0,
                        static_cast<int>(DUFF_FFMC_DEPTH * 10.0)>
{
public:
  FuelGrass() = delete;
  ~FuelGrass() = default;
  FuelGrass(const FuelGrass& rhs) noexcept = delete;
  FuelGrass(FuelGrass&& rhs) noexcept = delete;
  FuelGrass& operator=(const FuelGrass& rhs) noexcept = delete;
  FuelGrass& operator=(FuelGrass&& rhs) noexcept = delete;
  /**
   * \brief A grass fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param log_q Log value of q [ST-X-3 table 7]
   */
  constexpr FuelGrass(const FuelCodeSize& code,
                      const char* name,
                      const LogValue log_q)
  // HACK: grass assumes no duff (total duff depth == ffmc depth => dmc depth is 0)
    : StandardFuel<A, B, C, 1, 0, 0, 0, 0,
                   static_cast<int>(DUFF_FFMC_DEPTH * 10.0)>(code,
                                                             name,
															 false,
															 log_q,
															 &Duff::PeatMuck,
															 &Duff::PeatMuck)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 pg 21]
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 pg 21]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo&) const noexcept override
  {
    return DEFAULT_GRASS_FUEL_LOAD;
  }
  /**
   * \brief Calculate base rate of spread multiplier
   * \param nd Difference between date and the date of minimum foliar moisture content
   * \param wx FwiWeather to use for calculation
   * \return Base rate of spread multiplier
   */
  [[nodiscard]] static double baseMultiplier(const int nd,
                                             const wx::FwiWeather& wx) noexcept
  {
    const double curing = wx.dc().asDouble() > 500
                            ?  // we're in drought conditions
                            100
                            : calculate_grass_curing(nd);
    return BASE_MULTIPLIER_CURING(curing);
  }
  /**
   * \brief Calculate ISI with slope influence and zero wind (ISF) [ST-X-3 eq 41]
   * \param spread SpreadInfo to use
   * \param isi Initial Spread Index
   * \return ISI with slope influence and zero wind (ISF) [ST-X-3 eq 41]
   */
  [[nodiscard]] double calculateIsf(const SpreadInfo& spread,
                                    const double isi) const noexcept override
  {
    const auto mu = baseMultiplier(spread.nd(), *spread.weather());
    return this->limitIsf(min(0.001, mu), calculateRos(mu, isi) * spread.slopeFactor());
  }
  /**
   * \brief Calculate rate of spread (m/min)
   * \param nd Difference between date and the date of minimum foliar moisture content
   * \param wx FwiWeather to use for calculation
   * \param isi Initial Spread Index (may differ from wx because of slope)
   * \return Rate of spread (m/min)
   */
  [[nodiscard]] double calculateRos(const int nd,
                                    const wx::FwiWeather& wx,
                                    const double isi) const noexcept override
  {
    return calculateRos(baseMultiplier(nd, wx), isi);
  }
protected:
  /**
   * \brief Length to Breadth ratio [ST-X-3 eq 80/81]
   * \param ws Wind Speed (km/h)
   * \return Length to Breadth ratio [ST-X-3 eq 80/81]
   */
  [[nodiscard]] double lengthToBreadth(const double ws) const noexcept override
  {
    return LENGTH_TO_BREADTH_GRASS(ws);
  }
private:
  /**
   * \brief Calculate rate of spread (m/min)
   * \param multiplier Rate of spread multiplier
   * \param isi Initial Spread Index (may differ from wx because of slope)
   * \return Rate of spread (m/min)
   */
  [[nodiscard]] double calculateRos(const double multiplier,
                                    const double isi) const noexcept
  {
    return multiplier * this->rosBasic(isi);
  }
};
namespace fbp
{
/**
 * \brief FBP fuel type C-1.
 */
class FuelC1 : public FuelConifer<90, 649, 450, 72, 2, 75, 45, 5, 34>
{
public:
  FuelC1() = delete;
  ~FuelC1() = default;
  FuelC1(const FuelC1& rhs) noexcept = delete;
  FuelC1(FuelC1&& rhs) noexcept = delete;
  FuelC1& operator=(const FuelC1& rhs) noexcept = delete;
  FuelC1& operator=(FuelC1&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-1
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC1(const FuelCodeSize& code) noexcept
    : FuelConifer(code,
                  "C-1",
                  data::LOG_0_9,
                  &Duff::Reindeer,
                  &Duff::Peat)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [GLC-X-10 eq 9a/9b]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [GLC-X-10 eq 9a/9b]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override;
};
/**
 * \brief FBP fuel type C-2.
 */
class FuelC2 : public FuelConifer<110, 282, 150, 64, 3, 80, 34, 0, 100>
{
public:
  FuelC2() = delete;
  ~FuelC2() = default;
  FuelC2(const FuelC2& rhs) noexcept = delete;
  FuelC2(FuelC2&& rhs) noexcept = delete;
  FuelC2& operator=(const FuelC2& rhs) noexcept = delete;
  FuelC2& operator=(FuelC2&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-2
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC2(const FuelCodeSize& code) noexcept
    : FuelConifer(code,
                  "C-2",
                  data::LOG_0_7,
                  &Duff::SphagnumUpper)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 10]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 10]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override;
};
/**
 * \brief FBP fuel type C-3.
 */
class FuelC3 : public FuelJackpine<110, 444, 300, 62, 8, 115, 20, 65>
{
public:
  FuelC3() = delete;
  ~FuelC3() = default;
  FuelC3(const FuelC3& rhs) noexcept = delete;
  FuelC3(FuelC3&& rhs) noexcept = delete;
  FuelC3& operator=(const FuelC3& rhs) noexcept = delete;
  FuelC3& operator=(FuelC3&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-3
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC3(const FuelCodeSize& code) noexcept
    : FuelJackpine(code,
                   "C-3",
                   data::LOG_0_75,
                   &Duff::FeatherMoss,
                   &Duff::PineSeney)
  {
  }
};
/**
 * \brief FBP fuel type C-4.
 */
class FuelC4 : public FuelJackpine<110, 293, 150, 66, 4, 120, 31, 62>
{
public:
  FuelC4() = delete;
  ~FuelC4() = default;
  FuelC4(const FuelC4& rhs) noexcept = delete;
  FuelC4(FuelC4&& rhs) noexcept = delete;
  FuelC4& operator=(const FuelC4& rhs) noexcept = delete;
  FuelC4& operator=(FuelC4&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-4
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC4(const FuelCodeSize& code) noexcept
    : FuelJackpine(code,
                   "C-4",
                   data::LOG_0_8,
                   &Duff::PineSeney)
  {
  }
};
/**
 * \brief FBP fuel type C-5.
 */
class FuelC5 : public FuelPine<30, 697, 400, 56, 18, 120, 93, 46>
{
public:
  FuelC5() = delete;
  ~FuelC5() = default;
  FuelC5(const FuelC5& rhs) noexcept = delete;
  FuelC5(FuelC5&& rhs) noexcept = delete;
  FuelC5& operator=(const FuelC5& rhs) noexcept = delete;
  FuelC5& operator=(FuelC5&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-5
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC5(const FuelCodeSize& code) noexcept
    : FuelPine(code,
               "C-5",
               data::LOG_0_8,
               &Duff::PineSeney)
  {
  }
};
/**
 * \brief FBP fuel type C-6.
 */
class FuelC6 : public FuelPine<30, 800, 300, 62, 7, 180, 50, 50>
{
public:
  FuelC6() = delete;
  ~FuelC6() = default;
  FuelC6(const FuelC6& rhs) noexcept = delete;
  FuelC6(FuelC6&& rhs) noexcept = delete;
  FuelC6& operator=(const FuelC6& rhs) noexcept = delete;
  FuelC6& operator=(FuelC6&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-6
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC6(const FuelCodeSize& code) noexcept
    : FuelPine(code,
               "C-6",
               data::LOG_0_8,
               &Duff::PineSeney)
  {
  }
protected:
  /**
   * \brief Final rate of spread (m/min)
   * \param spread SpreadInfo to use
   * \param isi Initial Spread Index (may differ from wx because of slope)
   * \param cfb Crown Fraction Burned (CFB) [ST-X-3 eq 58]
   * \param rss Surface Rate of spread (ROS) (m/min) [ST-X-3 eq 55]
   * \return Final rate of spread (m/min)
   */
  [[nodiscard]] double finalRos(const SpreadInfo& spread,
                                double isi,
                                double cfb,
                                double rss) const noexcept override;
};
/**
 * \brief FBP fuel type C-7.
 */
class FuelC7 : public FuelConifer<45, 305, 200, 106, 10, 50, 20, 15, 50>
{
public:
  FuelC7() = delete;
  ~FuelC7() = default;
  FuelC7(const FuelC7& rhs) noexcept = delete;
  FuelC7(FuelC7&& rhs) noexcept = delete;
  FuelC7& operator=(const FuelC7& rhs) noexcept = delete;
  FuelC7& operator=(FuelC7&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type C-7
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelC7(const FuelCodeSize& code) noexcept
    : FuelConifer(code,
                  "C-7",
                  data::LOG_0_85,
                  &Duff::SprucePine)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 15]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 15]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override;
};
/**
 * \brief FBP fuel type D-2.
 */
class FuelD2 : public FuelNonMixed<6, 232, 160, 32, 0, 0, 61, 59, 24>
{
public:
  FuelD2() = delete;
  ~FuelD2() = default;
  FuelD2(const FuelD2& rhs) noexcept = delete;
  FuelD2(FuelD2&& rhs) noexcept = delete;
  FuelD2& operator=(const FuelD2& rhs) noexcept = delete;
  FuelD2& operator=(FuelD2&& rhs) noexcept = delete;
  // HACK: assume same bulk_density and inorganicContent as D1
  /**
   * \brief FBP fuel type D-2
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelD2(const FuelCodeSize& code) noexcept
    : FuelNonMixed(code,
                   "D-2",
                   false,
                   data::LOG_0_9,
                   &Duff::Peat)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2)
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2)
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override;
  /**
   * \brief Calculate rate of spread (m/min)
   * \param nd Difference between date and the date of minimum foliar moisture content
   * \param wx FwiWeather to use for calculation
   * \param isi Initial Spread Index (may differ from wx because of slope)
   * \return Rate of spread (m/min)
   */
  [[nodiscard]] double calculateRos(int nd,
                                    const wx::FwiWeather& wx,
                                    double isi) const noexcept override;
};
/**
 * \brief FBP fuel type M-1.
 * \tparam PercentConifer Percent conifer
 */
template <int PercentConifer>
class FuelM1 : public FuelMixedWood<10, PercentConifer>
{
public:
  FuelM1() = delete;
  ~FuelM1() = default;
  FuelM1(const FuelM1& rhs) noexcept = delete;
  FuelM1(FuelM1&& rhs) noexcept = delete;
  FuelM1& operator=(const FuelM1& rhs) noexcept = delete;
  FuelM1& operator=(FuelM1&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type M-1
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   */
  constexpr FuelM1(const FuelCodeSize& code, const char* name)
    : FuelMixedWood<10, PercentConifer>(code, name)
  {
  }
};
/**
 * \brief FBP fuel type M-2.
 * \tparam PercentConifer Percent conifer
 */
template <int PercentConifer>
class FuelM2 : public FuelMixedWood<2, PercentConifer>
{
public:
  FuelM2() = delete;
  ~FuelM2() = default;
  FuelM2(const FuelM2& rhs) noexcept = delete;
  FuelM2(FuelM2&& rhs) noexcept = delete;
  FuelM2& operator=(const FuelM2& rhs) noexcept = delete;
  FuelM2& operator=(FuelM2&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type M-2
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   */
  constexpr FuelM2(const FuelCodeSize& code, const char* name)
    : FuelMixedWood<2, PercentConifer>(code, name)
  {
  }
};
/**
 * \brief FBP fuel type M-3.
 * \tparam PercentDeadFir Percent dead fir
 */
template <int PercentDeadFir>
class FuelM3 : public FuelMixedDead<120, 572, 140, 50, 10, PercentDeadFir>
{
public:
  FuelM3() = delete;
  ~FuelM3() = default;
  FuelM3(const FuelM3& rhs) noexcept = delete;
  FuelM3(FuelM3&& rhs) noexcept = delete;
  FuelM3& operator=(const FuelM3& rhs) noexcept = delete;
  FuelM3& operator=(FuelM3&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type M-3
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   */
  constexpr FuelM3(const FuelCodeSize& code, const char* name)
    : FuelMixedDead<120, 572, 140, 50, 10, PercentDeadFir>(code,
                                                           name,
														   data::LOG_0_8)
  {
  }
};
/**
 * \brief FBP fuel type M-4.
 * \tparam PercentDeadFir Percent dead fir
 */
template <int PercentDeadFir>
class FuelM4 : public FuelMixedDead<100, 404, 148, 50, 2, PercentDeadFir>
{
public:
  FuelM4() = delete;
  ~FuelM4() = default;
  FuelM4(const FuelM4& rhs) noexcept = delete;
  FuelM4(FuelM4&& rhs) noexcept = delete;
  FuelM4& operator=(const FuelM4& rhs) noexcept = delete;
  FuelM4& operator=(FuelM4&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type M-4
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   */
  constexpr FuelM4(const FuelCodeSize& code, const char* name)
    : FuelMixedDead<100, 404, 148, 50, 2, PercentDeadFir>(code,
                                                          name,
														  data::LOG_0_8)
  {
  }
};
/**
 * \brief FBP fuel type O-1a.
 */
class FuelO1A : public FuelGrass<190, 310, 140>
{
public:
  FuelO1A() = delete;
  ~FuelO1A() = default;
  FuelO1A(const FuelO1A& rhs) noexcept = delete;
  FuelO1A(FuelO1A&& rhs) noexcept = delete;
  FuelO1A& operator=(const FuelO1A& rhs) noexcept = delete;
  FuelO1A& operator=(FuelO1A&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type O-1a.
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelO1A(const FuelCodeSize& code) noexcept
    : FuelGrass(code, "O-1a", data::LOG_1_0)
  {
  }
};
/**
 * \brief FBP fuel type O-1b.
 */
class FuelO1B : public FuelGrass<250, 350, 170>
{
public:
  FuelO1B() = delete;
  ~FuelO1B() = default;
  FuelO1B(const FuelO1B& rhs) noexcept = delete;
  FuelO1B(FuelO1B&& rhs) noexcept = delete;
  FuelO1B& operator=(const FuelO1B& rhs) noexcept = delete;
  FuelO1B& operator=(FuelO1B&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type O-1b.
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelO1B(const FuelCodeSize& code) noexcept
    : FuelGrass(code, "O-1b", data::LOG_1_0)
  {
  }
};
}
/**
 * \brief A slash fuel type.
 * \tparam A Rate of spread parameter a [ST-X-3 table 6]
 * \tparam B Rate of spread parameter b * 10000 [ST-X-3 table 6]
 * \tparam C Rate of spread parameter c * 100 [ST-X-3 table 6]
 * \tparam Bui0 Average Build-up Index for the fuel type [ST-X-3 table 7]
 * \tparam FfcA Forest Floor Consumption parameter a [ST-X-3 eq 19/21/23]
 * \tparam FfcB Forest Floor Consumption parameter b * 10000 [ST-X-3 eq 19/21/23]
 * \tparam WfcA Woody Fuel Consumption parameter a [ST-X-3 eq 20/22/24]
 * \tparam WfcB Woody Fuel Consumption parameter b * 10000 [ST-X-3 eq 20/22/24]
 * \tparam BulkDensity Crown bulk density * 1000 [Anderson table 1]
 */
template <int A, int B, int C, int Bui0, int FfcA, int FfcB, int WfcA, int WfcB, int
          BulkDensity>
class FuelSlash : public FuelConifer<A, B, C, Bui0, 0, 0, BulkDensity, 15, 74>
{
public:
  FuelSlash() = delete;
  ~FuelSlash() = default;
  FuelSlash(const FuelSlash& rhs) noexcept = delete;
  FuelSlash(FuelSlash&& rhs) noexcept = delete;
  FuelSlash& operator=(const FuelSlash& rhs) noexcept = delete;
  FuelSlash& operator=(FuelSlash&& rhs) noexcept = delete;
  /**
   * \brief A slash fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param log_q Log value of q [ST-X-3 table 7]
   * \param duff_ffmc Type of duff near the surface
   * \param duff_dmc Type of duff deeper underground
   */
  constexpr FuelSlash(const FuelCodeSize& code,
                      const char* name,
                      const LogValue log_q,
                      const Duff* duff_ffmc,
                      const Duff* duff_dmc)
    : FuelConifer<A, B, C, Bui0, 0, 0, BulkDensity, 15, 74>(code,
                                                            name,
															log_q,
															duff_ffmc,
															duff_dmc)
  {
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 25]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 25]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const noexcept override
  {
    return ffcA() * (1.0 - exp(ffcB() * spread.bui().asDouble()))
      + wfcA() * (1.0 - exp(wfcB() * spread.bui().asDouble()));
  }
private:
  /**
   * \brief Forest Floor Consumption parameter a [ST-X-3 eq 19/21/23]
   * \return Forest Floor Consumption parameter a [ST-X-3 eq 19/21/23]
   */
  [[nodiscard]] static constexpr double ffcA() { return FfcA; }
  /**
   * \brief Forest Floor Consumption parameter b [ST-X-3 eq 19/21/23]
   * \return Forest Floor Consumption parameter b [ST-X-3 eq 19/21/23]
   */
  [[nodiscard]] static constexpr double ffcB() { return FfcB / 10000.0; }
  /**
   * \brief Woody Fuel Consumption parameter a [ST-X-3 eq 20/22/24]
   * \return Woody Fuel Consumption parameter a [ST-X-3 eq 20/22/24]
   */
  [[nodiscard]] static constexpr double wfcA() { return WfcA; }
  /**
   * \brief Woody Fuel Consumption parameter b [ST-X-3 eq 20/22/24]
   * \return Woody Fuel Consumption parameter b [ST-X-3 eq 20/22/24]
   */
  [[nodiscard]] static constexpr double wfcB() { return WfcB / 10000.0; }
};
namespace fbp
{
/**
 * \brief FBP fuel type S-1.
 */
class FuelS1 : public FuelSlash<75, 297, 130, 38, 4, -250, 4, -340, 78>
{
public:
  FuelS1() = delete;
  ~FuelS1() = default;
  FuelS1(const FuelS1& rhs) noexcept = delete;
  FuelS1(FuelS1&& rhs) noexcept = delete;
  FuelS1& operator=(const FuelS1& rhs) noexcept = delete;
  FuelS1& operator=(FuelS1&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type S-1
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelS1(const FuelCodeSize& code) noexcept
    : FuelSlash(code,
                "S-1",
                data::LOG_0_75,
                &Duff::FeatherMoss,
                &Duff::PineSeney)
  {
  }
};
/**
 * \brief FBP fuel type S-2.
 */
class FuelS2 : public FuelSlash<40, 438, 170, 63, 10, -130, 6, -600, 132>
{
public:
  FuelS2() = delete;
  ~FuelS2() = default;
  FuelS2(const FuelS2& rhs) noexcept = delete;
  FuelS2(FuelS2&& rhs) noexcept = delete;
  FuelS2& operator=(const FuelS2& rhs) noexcept = delete;
  FuelS2& operator=(FuelS2&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type S-2
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelS2(const FuelCodeSize& code) noexcept
    : FuelSlash(code,
                "S-2",
                data::LOG_0_75,
                &Duff::FeatherMoss,
                &Duff::WhiteSpruce)
  {
  }
};
/**
 * \brief FBP fuel type S-3.
 */
class FuelS3 : public FuelSlash<55, 829, 320, 31, 12, -166, 20, -210, 100>
{
public:
  FuelS3() = delete;
  ~FuelS3() = default;
  FuelS3(const FuelS3& rhs) noexcept = delete;
  FuelS3(FuelS3&& rhs) noexcept = delete;
  FuelS3& operator=(const FuelS3& rhs) noexcept = delete;
  FuelS3& operator=(FuelS3&& rhs) noexcept = delete;
  /**
   * \brief FBP fuel type S-3
   * \param code Code to identify fuel with
   */
  explicit constexpr FuelS3(const FuelCodeSize& code) noexcept
    : FuelSlash(code,
                "S-3",
                data::LOG_0_75,
                &Duff::FeatherMoss,
                &Duff::PineSeney)
  {
  }
};
}
template <class FuelSpring, class FuelSummer>
class FuelVariable;
template <class FuelSpring, class FuelSummer>
[[nodiscard]] const FuelType& find_fuel_by_season(const int nd,
                                                  const FuelVariable<
                                                    FuelSpring, FuelSummer>& fuel)
noexcept
{
  return calculate_is_green(nd)
           ? fuel.spring()
           : fuel.summer();
}
template <class FuelSpring, class FuelSummer>
[[nodiscard]] double compare_by_season(const FuelVariable<FuelSpring, FuelSummer>& fuel,
                                       const function<double(const FuelType&)> fct)
{
  // HACK: no way to tell which is which, so let's assume they have to be the same??
  // HACK: use a function so that DEBUG section doesn't get out of sync
  const auto for_spring = fct(fuel.spring());
#ifndef NDEBUG
			const auto for_summer = fct(fuel.summer());
			logging::check_fatal(for_spring != for_summer, "Expected spring and summer cfb to be identical");
#endif
  return for_spring;
}
/**
 * \brief A fuel type that changes based on the season.
 * \tparam FuelSpring Fuel type to use in the spring
 * \tparam FuelSummer Fuel type to use in the summer
 */
template <class FuelSpring, class FuelSummer>
class FuelVariable : public FuelType
{
public:
  // don't delete pointers since they're handled elsewhere
  ~FuelVariable() = default;
  /**
   * \brief A slash fuel type
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param can_crown Whether or not this fuel can have a crown fire
   * \param spring Fuel type to use in the spring
   * \param summer Fuel type to use in the summer
   */
  constexpr FuelVariable(const FuelCodeSize& code,
                         const char* name,
                         const bool can_crown,
                         const FuelSpring* const spring,
                         const FuelSummer* const summer)
    : FuelType(code, name, can_crown),
      spring_(spring),
      summer_(summer)
  {
  }
  FuelVariable(FuelVariable&& rhs) noexcept = delete;
  FuelVariable(const FuelVariable& rhs) = delete;
  FuelVariable& operator=(FuelVariable&& rhs) noexcept = delete;
  FuelVariable& operator=(const FuelVariable& rhs) = delete;
  /**
   * \brief BUI Effect on surface fire rate of spread [ST-X-3 eq 54]
   * \param bui Build-up Index
   * \return BUI Effect on surface fire rate of spread [ST-X-3 eq 54]
   */
  [[nodiscard]] double buiEffect(double bui) const override
  {
    const function<double(const FuelType&)> fct = [bui](const FuelType& fuel)
    {
      return fuel.buiEffect(bui);
    };
    return compare_by_season(*this, fct);
  }
  /**
   * \brief Crown Fuel Consumption (CFC) (kg/m^2) [ST-X-3 eq 66]
   * \param cfb Crown Fraction Burned (CFB) [ST-X-3 eq 58]
   * \return Crown Fuel Consumption (CFC) (kg/m^2) [ST-X-3 eq 66]
   */
  [[nodiscard]] double crownConsumption(const double cfb) const override
  {
    const function<double(const FuelType&)> fct = [cfb](const FuelType& fuel)
    {
      return fuel.crownConsumption(cfb);
    };
    return compare_by_season(*this, fct);
  }
  /**
   * \brief Initial rate of spread (m/min) [ST-X-3 eq 26]
   * \param nd Difference between date and the date of minimum foliar moisture content
   * \param wx FwiWeather to use
   * \param isi Initial Spread Index
   * \return Initial rate of spread (m/min) [ST-X-3 eq 26]
   */
  [[nodiscard]] double calculateRos(const int nd,
                                    const wx::FwiWeather& wx,
                                    const double isi) const override
  {
    return find_fuel_by_season(nd, *this).calculateRos(nd, wx, isi);
  }
  /**
   * \brief Calculate ISI with slope influence and zero wind (ISF) [ST-X-3 eq 41]
   * \param spread SpreadInfo to use
   * \param isi Initial Spread Index
   * \return ISI with slope influence and zero wind (ISF) [ST-X-3 eq 41]
   */
  [[nodiscard]] double calculateIsf(const SpreadInfo& spread,
                                    const double isi) const
  override
  {
    return find_fuel_by_season(spread.nd(), *this).calculateIsf(spread, isi);
  }
  /**
   * \brief Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 9-25]
   * \param spread SpreadInfo to use
   * \return Surface Fuel Consumption (SFC) (kg/m^2) [ST-X-3 eq 9-25]
   */
  [[nodiscard]] double surfaceFuelConsumption(
    const SpreadInfo& spread) const override
  {
    return find_fuel_by_season(spread.nd(), *this).surfaceFuelConsumption(spread);
  }
  /**
   * \brief Length to Breadth ratio [ST-X-3 eq 79]
   * \param ws Wind Speed (km/h)
   * \return Length to Breadth ratio [ST-X-3 eq 79]
   */
  [[nodiscard]] double lengthToBreadth(const double ws) const override
  {
    const function<double(const FuelType&)> fct = [ws](const FuelType& fuel)
    {
      return fuel.lengthToBreadth(ws);
    };
    return compare_by_season(*this, fct);
  }
  /**
   * \brief Final rate of spread (m/min)
   * \param spread SpreadInfo to use
   * \param isi Initial Spread Index (may differ from wx because of slope)
   * \param cfb Crown Fraction Burned (CFB) [ST-X-3 eq 58]
   * \param rss Surface Rate of spread (ROS) (m/min) [ST-X-3 eq 55]
   * \return Final rate of spread (m/min)
   */
  [[nodiscard]] double finalRos(const SpreadInfo& spread,
                                const double isi,
                                const double cfb,
                                const double rss) const override
  {
    return find_fuel_by_season(spread.nd(), *this).finalRos(spread, isi, cfb, rss);
  }
  /**
   * \brief Critical Surface Fire Intensity (CSI) [ST-X-3 eq 56]
   * \param spread SpreadInfo to use in calculation
   * \return Critical Surface Fire Intensity (CSI) [ST-X-3 eq 56]
   */
  [[nodiscard]] double criticalSurfaceIntensity(
    const SpreadInfo& spread) const override
  {
    return find_fuel_by_season(spread.nd(), *this).criticalSurfaceIntensity(spread);
  }
  /**
   * \brief Crown Fraction Burned (CFB) [ST-X-3 eq 58]
   * \param rss Surface Rate of spread (ROS) (m/min) [ST-X-3 eq 55]
   * \param rso Critical surface fire spread rate (RSO) [ST-X-3 eq 57]
   * \return Crown Fraction Burned (CFB) [ST-X-3 eq 58]
   */
  [[nodiscard]] double crownFractionBurned(const double rss,
                                           const double rso) const noexcept override
  {
    return spring().crownFractionBurned(rss, rso);
  }
  /**
   * \brief Calculate probability of burning [Anderson eq 1]
   * \param mc_fraction moisture content (% / 100)
   * \return Calculate probability of burning [Anderson eq 1]
   */
  [[nodiscard]] double probabilityPeat(const double mc_fraction) const noexcept override
  {
    return spring().probabilityPeat(mc_fraction);
  }
  /**
   * \brief Survival probability calculated using probability of ony survival based on multiple formulae
   * \param wx FwiWeather to calculate survival probability for
   * \return Chance of survival (% / 100)
   */
  [[nodiscard]] double survivalProbability(const wx::FwiWeather& wx) const noexcept
  override
  {
    return spring().survivalProbability(wx);
  }
  /**
   * \brief Fuel to use before green-up
   * \return Fuel to use before green-up
   */
  [[nodiscard]] constexpr const FuelType& spring() const { return *spring_; }
  /**
   * \brief Fuel to use after green-up
   * \return Fuel to use after green-up
   */
  [[nodiscard]] constexpr const FuelType& summer() const { return *summer_; }
private:
  /**
   * \brief Fuel to use before green-up
   */
  const FuelSpring* const spring_;
  /**
   * \brief Fuel to use after green-up
   */
  const FuelSummer* const summer_;
};
namespace fbp
{
/**
 * \brief FBP fuel type D-1/D-2.
 */
class FuelD1D2 : public FuelVariable<FuelD1, FuelD2>
{
public:
  FuelD1D2() = delete;
  ~FuelD1D2() = default;
  FuelD1D2(const FuelD1D2& rhs) noexcept = delete;
  FuelD1D2(FuelD1D2&& rhs) noexcept = delete;
  FuelD1D2& operator=(const FuelD1D2& rhs) noexcept = delete;
  FuelD1D2& operator=(FuelD1D2&& rhs) noexcept = delete;
  /**
   * \brief A fuel that changes between D-1/D-2 depending on green-up
   * \param code Code to identify fuel with
   * \param d1 D-1 fuel to use before green-up
   * \param d2 D-2 fuel to use after green-up
   */
  constexpr FuelD1D2(const FuelCodeSize& code,
                     const FuelD1* d1,
                     const FuelD2* d2) noexcept
    : FuelVariable(code, "D-1/D-2", false, d1, d2)
  {
  }
};
/**
 * \brief FBP fuel type M-1/M-2.
 * \tparam PercentConifer Percent conifer
 */
template <int PercentConifer>
class FuelM1M2 : public FuelVariable<FuelM1<PercentConifer>, FuelM2<PercentConifer>>
{
public:
  FuelM1M2() = delete;
  ~FuelM1M2() = default;
  FuelM1M2(const FuelM1M2& rhs) noexcept = delete;
  FuelM1M2(FuelM1M2&& rhs) noexcept = delete;
  FuelM1M2& operator=(const FuelM1M2& rhs) noexcept = delete;
  FuelM1M2& operator=(FuelM1M2&& rhs) noexcept = delete;
  // HACK: it's up to you to make sure these match
  /**
   * \brief A fuel that changes between M-1/M-2 depending on green-up
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param m1 M-1 fuel to use before green-up
   * \param m2 M-2 fuel to use after green-up
   */
  constexpr FuelM1M2(const FuelCodeSize& code,
                     const char* name,
                     const FuelM1<PercentConifer>* m1,
                     const FuelM2<PercentConifer>* m2)
    : FuelVariable<FuelM1<PercentConifer>, FuelM2<PercentConifer>>(code, name, true, m1, m2)
  {
  }
};
/**
 * \brief FBP fuel type M-3/M-4.
 * \tparam PercentDeadFir Percent dead fir
 */
template <int PercentDeadFir>
class FuelM3M4 : public FuelVariable<FuelM3<PercentDeadFir>, FuelM4<PercentDeadFir>>
{
public:
  FuelM3M4() = delete;
  ~FuelM3M4() = default;
  FuelM3M4(const FuelM3M4& rhs) noexcept = delete;
  FuelM3M4(FuelM3M4&& rhs) noexcept = delete;
  FuelM3M4& operator=(const FuelM3M4& rhs) noexcept = delete;
  FuelM3M4& operator=(FuelM3M4&& rhs) noexcept = delete;
  /**
   * \brief A fuel that changes between M-3/M-4 depending on green-up
   * \param code Code to identify fuel with
   * \param name Name of the fuel
   * \param m3 M-3 fuel to use before green-up
   * \param m4 M-4 fuel to use after green-up
   */
  constexpr FuelM3M4(const FuelCodeSize& code,
                     const char* name,
                     const FuelM3<PercentDeadFir>* m3,
                     const FuelM4<PercentDeadFir>* m4)
    : FuelVariable<FuelM3<PercentDeadFir>, FuelM4<PercentDeadFir>>(code, name, true, m3, m4)
  {
  }
};
}
}
}
