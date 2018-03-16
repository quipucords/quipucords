import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';

import { Button, Filter, Sort, Toolbar } from 'patternfly-react';

import helpers from '../../common/helpers';
import Store from '../../redux/store';

import { viewToolbarTypes } from '../../redux/constants';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import RefreshTimeButton from '../refreshTimeButton/refreshTimeButton';

class ViewToolbar extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
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

    if (_.size(filterFields)) {
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

    return null;
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
          <SimpleTooltip id="sortTip" tooltip={`Sort by ${sortType.title}`}>
            <Sort.DirectionSelector
              isNumeric={sortType.isNumeric}
              isAscending={sortAscending}
              onClick={() => this.toggleCurrentSortDirection()}
            />
          </SimpleTooltip>
        </Sort>
      );
    }

    return null;
  }

  renderRefresh() {
    const { onRefresh, lastRefresh } = this.props;

    return (
      <div className="form-group">
        <RefreshTimeButton onRefresh={onRefresh} lastRefresh={lastRefresh} />
      </div>
    );
  }

  renderCounts() {
    const { totalCount, selectedCount, itemsType, itemsTypePlural } = this.props;

    return (
      <h5 className="quipucords-view-count">
        {selectedCount > 0 ? `${selectedCount} of ` : null}
        {`${totalCount} ${totalCount === 1 ? itemsType : itemsTypePlural}`}
        {selectedCount > 0 ? ' selected' : ''}
      </h5>
    );
  }

  renderActiveFilters() {
    const { activeFilters } = this.props;

    if (_.size(activeFilters)) {
      return [
        <Filter.ActiveLabel key="label">Active Filters:</Filter.ActiveLabel>,
        <Filter.List key="list">
          {activeFilters.map((item, index) => {
            return (
              <Filter.Item key={index} onRemove={this.removeFilter} filterData={item}>
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

    return <Filter.ActiveLabel>No Filters</Filter.ActiveLabel>;
  }

  render() {
    const { actions } = this.props;

    return (
      <Toolbar>
        {this.renderFilter()}
        {this.renderSort()}
        {this.renderRefresh()}
        <Toolbar.RightContent>{actions}</Toolbar.RightContent>
        <Toolbar.Results>
          {this.renderActiveFilters()}
          {this.renderCounts()}
        </Toolbar.Results>
      </Toolbar>
    );
  }
}

ViewToolbar.propTypes = {
  viewType: PropTypes.string,
  totalCount: PropTypes.number,
  selectedCount: PropTypes.number,
  filterFields: PropTypes.array,
  sortFields: PropTypes.array,
  onRefresh: PropTypes.func,
  lastRefresh: PropTypes.number,
  actions: PropTypes.node,
  itemsType: PropTypes.string,
  itemsTypePlural: PropTypes.string,
  filterType: PropTypes.object,
  filterValue: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

ViewToolbar.defaultProps = {
  filteredCount: -1
};

export default ViewToolbar;
