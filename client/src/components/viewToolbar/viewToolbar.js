import PropTypes from 'prop-types';
import React from 'react';

import { Button, Filter, Sort, Toolbar } from 'patternfly-react';

import { bindMethods } from '../../common/helpers';
import Store from '../../redux/store';

import { viewToolbarTypes } from '../../redux/constants';

class ViewToolbar extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'updateCurrentValue',
      'onValueKeyPress',
      'selectFilterType',
      'filterValueSelected',
      'filterAdded',
      'removeFilter',
      'clearFilters',
      'updateCurrentSortType',
      'toggleCurrentSortDirection'
    ]);
  }

  componentDidMount() {
    const { filterType, sortType, filterFields, sortFields } = this.props;

    if (!filterType) {
      this.selectFilterType(filterFields[0]);
    }

    if (!sortType) {
      this.updateCurrentSortType(sortFields[0]);
    }
  }

  filterAdded(field, value) {
    const { viewType } = this.props;

    let filterText = '';
    if (field.title) {
      filterText = field.title;
    } else {
      filterText = field;
    }
    filterText += ': ';

    if (value.title) {
      filterText += value.title;
    } else {
      filterText += value;
    }

    let filter = { field: field, value: value, label: filterText };
    Store.dispatch({
      type: viewToolbarTypes.ADD_FILTER,
      viewType: viewType,
      filter
    });
  }

  selectFilterType(filterType) {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_TYPE,
      viewType: viewType,
      filterType
    });
  }

  filterValueSelected(newFilterValue) {
    const { filterType, viewType } = this.props;

    let filterValue = newFilterValue;
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_VALUE,
      viewType: viewType,
      filterValue
    });
    if (newFilterValue) {
      this.filterAdded(filterType, newFilterValue);
    }
  }

  updateCurrentValue(event) {
    const { viewType } = this.props;

    let filterValue = event.target.value;
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_VALUE,
      viewType: viewType,
      filterValue
    });
  }

  onValueKeyPress(keyEvent) {
    const { filterType, filterValue } = this.props;

    if (keyEvent.key === 'Enter' && filterValue && filterValue.length) {
      this.filterAdded(filterType, filterValue);
      keyEvent.stopPropagation();
      keyEvent.preventDefault();
    }
  }

  removeFilter(filter) {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.REMOVE_FILTER,
      viewType: viewType,
      filter
    });
  }

  clearFilters() {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType: viewType
    });
  }

  updateCurrentSortType(sortType) {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.SET_SORT_TYPE,
      viewType: viewType,
      sortType
    });
  }

  toggleCurrentSortDirection() {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.TOGGLE_SORT_ASCENDING,
      viewType: viewType
    });
  }

  renderFilterInput() {
    const { filterType, filterValue } = this.props;
    if (!filterType) {
      return null;
    }

    if (filterType.filterType === 'select') {
      return (
        <Filter.ValueSelector
          filterValues={filterType.filterValues}
          currentValue={filterValue}
          placeholder={filterType.placeholder}
          onFilterValueSelected={this.filterValueSelected}
        />
      );
    }

    return (
      <input
        className="form-control"
        type={filterType.filterType}
        value={filterValue}
        placeholder={filterType.placeholder}
        onChange={e => this.updateCurrentValue(e)}
        onKeyPress={e => this.onValueKeyPress(e)}
      />
    );
  }

  renderFilter() {
    const { filterType, filterFields } = this.props;

    return (
      <Filter>
        <Filter.TypeSelector
          filterTypes={filterFields}
          currentFilterType={filterType}
          onFilterTypeSelected={this.selectFilterType}
        />
        {this.renderFilterInput()}
      </Filter>
    );
  }

  renderSort() {
    const { sortType, sortAscending, sortFields } = this.props;

    if (sortType) {
      return (
        <Sort>
          <Sort.TypeSelector
            sortTypes={sortFields}
            currentSortType={sortType}
            onSortTypeSelected={this.updateCurrentSortType}
          />
          <Sort.DirectionSelector
            isNumeric={sortType.isNumeric}
            isAscending={sortAscending}
            onClick={() => this.toggleCurrentSortDirection()}
          />
        </Sort>
      );
    }

    return null;
  }

  renderCounts() {
    const {
      activeFilters,
      totalCount,
      filteredCount,
      itemsType,
      itemsTypePlural
    } = this.props;

    return (
      <h5>
        {activeFilters && activeFilters.length > 0
          ? `${filteredCount} of `
          : null}
        {totalCount + ' ' + (totalCount === 1 ? itemsType : itemsTypePlural)}
      </h5>
    );
  }

  renderActiveFilters() {
    const { activeFilters } = this.props;

    if (activeFilters && activeFilters.length) {
      return [
        <Filter.ActiveLabel key="label">
          {'Active Filters:'}
        </Filter.ActiveLabel>,
        <Filter.List key="list">
          {activeFilters.map((item, index) => {
            return (
              <Filter.Item
                key={index}
                onRemove={this.removeFilter}
                filterData={item}
              >
                {item.label}
              </Filter.Item>
            );
          })}
        </Filter.List>,
        <Button bsStyle="link" key="clear" onClick={this.clearFilters}>
          Clear All Filters
        </Button>
      ];
    }

    return null;
  }

  render() {
    const { actions } = this.props;

    return (
      <Toolbar>
        {this.renderFilter()}
        {this.renderSort()}
        <Toolbar.RightContent>{actions}</Toolbar.RightContent>
        <Toolbar.Results>
          {this.renderCounts()}
          {this.renderActiveFilters()}
        </Toolbar.Results>
      </Toolbar>
    );
  }
}

ViewToolbar.propTypes = {
  viewType: PropTypes.string,
  totalCount: PropTypes.number,
  filteredCount: PropTypes.number,
  filterFields: PropTypes.array,
  sortFields: PropTypes.array,
  actions: PropTypes.node,
  itemsType: PropTypes.string,
  itemsTypePlural: PropTypes.string,
  filterType: PropTypes.object,
  filterValue: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

export default ViewToolbar;
