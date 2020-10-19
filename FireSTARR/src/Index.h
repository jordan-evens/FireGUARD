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
namespace firestarr::data
{
/**
 * \brief A wrapper around a double to ensure correct types are used.
 * \tparam T The derived class that this Index represents.
 */
template <class T>
class Index
{
  /**
   * \brief Value represented by this
   */
  double value_;
public:
  /**
   * \brief Destructor
   */
  ~Index() = default;
  /**
   * \brief Construct with a value of 0
   */
  constexpr Index() noexcept
    : value_(0)
  {
  }
  /**
   * \brief Construct with given value
   * \param value Value to assign
   */
  constexpr explicit Index(const double value) noexcept
    : value_(value)
  {
  }
  /**
   * \brief Move constructor
   * \param rhs Index to move from
   */
  constexpr Index(Index<T>&& rhs) noexcept = default;
  /**
   * \brief Copy constructor
   * \param rhs Index to copy from
   */
  constexpr Index(const Index<T>& rhs) noexcept = default;
  /**
   * \brief Move assignment
   * \param rhs Index to move from
   * \return This, after assignment
   */
  Index<T>& operator=(Index<T>&& rhs) noexcept = default;
  /**
   * \brief Copy assignment
   * \param rhs Index to copy from
   * \return This, after assignment
   */
  Index<T>& operator=(const Index<T>& rhs) noexcept = default;
  /**
   * \brief Equality operator
   * \param rhs Index to compare to
   * \return Whether or not these are equivalent
   */
  [[nodiscard]] constexpr bool operator==(const Index<T>& rhs) const noexcept
  {
    return value_ == rhs.value_;
  }
  /**
   * \brief Not equals operator
   * \param rhs Index to compare to
   * \return Whether or not these are not equivalent
   */
  [[nodiscard]] constexpr bool operator!=(const Index<T>& rhs) const noexcept
  {
    return !(*this == rhs);
  }
  /**
   * \brief Returns value as a double
   * \return double value for Index
   */
  [[nodiscard]] constexpr double asDouble() const noexcept { return value_; }
  /**
   * \brief Less than operator
   * \param rhs Index to compare to
   * \return Whether or not this is less than the provided Index
   */
  constexpr bool operator<(const Index<T> rhs) const noexcept
  {
    return value_ < rhs.value_;
  }
  /**
   * \brief Greater than operator
   * \param rhs Index to compare to
   * \return Whether or not this is greater than the provided Index
   */
  [[nodiscard]] constexpr bool operator>(const Index<T> rhs) const noexcept
  {
    return value_ > rhs.value_;
  }
  /**
   * \brief Less than or equal to operator
   * \param rhs Index to compare to
   * \return Whether or not this is less than or equal to the provided Index
   */
  [[nodiscard]] constexpr bool operator<=(const Index<T> rhs) const noexcept
  {
    return value_ <= rhs.value_;
  }
  /**
   * \brief Greater than or equal to operator
   * \param rhs Index to compare to
   * \return Whether or not this is greater than or equal to the provided Index
   */
  [[nodiscard]] constexpr bool operator>=(const Index<T> rhs) const noexcept
  {
    return value_ >= rhs.value_;
  }
  /**
   * \brief Addition operator
   * \param rhs Index to add value from
   * \return The value of this plus the value of the provided index
   */
  [[nodiscard]] constexpr Index<T> operator+(const Index<T> rhs) const noexcept
  {
    return Index<T>(value_ + rhs.value_);
  }
  /**
   * \brief Subtraction operator
   * \param rhs Index to add value from
   * \return The value of this minus the value of the provided index
   */
  [[nodiscard]] constexpr Index<T> operator-(const Index<T> rhs) const noexcept
  {
    return Index<T>(value_ - rhs.value_);
  }
  /**
   * \brief Addition assignment operator
   * \param rhs Index to add value from
   * \return This, plus the value of the provided Index
   */
  constexpr Index<T>& operator+=(const Index<T> rhs) noexcept
  {
    value_ += rhs.value_;
    return *this;
  }
  /**
   * \brief Subtraction assignment operator
   * \param rhs Index to add value from
   * \return This, minus the value of the provided Index
   */
  constexpr Index<T>& operator-=(const Index<T> rhs) noexcept
  {
    value_ -= rhs.value_;
    return *this;
  }
};
/**
 * \brief A result of calling log(x) for some value of x, pre-calculated at compile time.
 */
class LogValue
  : public Index<LogValue>
{
public:
  //! @cond Doxygen_Suppress
  using Index::Index;
  //! @endcond
};
static constexpr LogValue LOG_0_7{-0.15490195998574316928778374140736};
static constexpr LogValue LOG_0_75{-0.12493873660829995313244988619387};
static constexpr LogValue LOG_0_8{-0.09691001300805641435878331582652};
static constexpr LogValue LOG_0_85{-0.07058107428570726667356900039616};
static constexpr LogValue LOG_0_9{-0.04575749056067512540994419348977};
static constexpr LogValue LOG_1_0{0};
}
