import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';

import { Button, Filter, Sort, Toolbar } from 'patternfly-react';

import { bindMethods } from '../../common/helpers';

import { SourceFilterFields } from './sourceFilterFields';
import { SourceSortFields } from './sourceSortFields';
import Store from '../../redux/store';
import * as dispatchTypes from '../../redux/constants/sourcesToolbarConstants';

class SourcesToolbar extends React.Component {
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
    const { filterType, sortType } = this.props;

    if (!filterType) {
      this.selectFilterType(SourceFilterFields[0]);
    }

    if (!sortType) {
      this.updateCurrentSortType(SourceSortFields[0]);
    }
  }

  filterAdded(field, value) {
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
      type: dispatchTypes.ADD_FILTER,
      filter
    });
  }

  selectFilterType(filterType) {
    Store.dispatch({
      type: dispatchTypes.SET_FILTER_TYPE,
      filterType
    });
  }

  filterValueSelected(newFilterValue) {
    const { filterType } = this.props;

    let filterValue = newFilterValue;
    Store.dispatch({
      type: dispatchTypes.SET_FILTER_VALUE,
      filterValue
    });
    if (newFilterValue) {
      this.filterAdded(filterType, newFilterValue);
    }
  }

  updateCurrentValue(event) {
    let filterValue = event.target.value;
    Store.dispatch({
      type: dispatchTypes.SET_FILTER_VALUE,
      filterValue
    });
  }

  onValueKeyPress(keyEvent) {
    const { filterValue, filterType } = this.props;

    if (keyEvent.key === 'Enter' && filterValue && filterValue.length > 0) {
      this.filterAdded(filterType, filterValue);
      keyEvent.stopPropagation();
      keyEvent.preventDefault();
    }
  }

  removeFilter(filter) {
    Store.dispatch({
      type: dispatchTypes.REMOVE_FILTER,
      filter
    });
  }

  clearFilters() {
    Store.dispatch({
      type: dispatchTypes.CLEAR_FILTERS
    });
  }

  updateCurrentSortType(sortType) {
    Store.dispatch({
      type: dispatchTypes.SET_SORT_TYPE,
      sortType
    });
  }

  toggleCurrentSortDirection() {
    Store.dispatch({
      type: dispatchTypes.TOGGLE_SORT_ASCENDING
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
    } else {
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
  }

  renderFilter() {
    const { filterType } = this.props;

    return (
      <Filter>
        <Filter.TypeSelector
          filterTypes={SourceFilterFields}
          currentFilterType={filterType}
          onFilterTypeSelected={this.selectFilterType}
        />
        {this.renderFilterInput()}
      </Filter>
    );
  }

  renderSort() {
    const { sortType, sortAscending } = this.props;

    if (sortType) {
      return (
        <Sort>
          <Sort.TypeSelector
            sortTypes={SourceSortFields}
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
    } else {
      return null;
    }
  }

  renderActions() {
    return (
      <div className="form-group">
        <Button className="unavailable">Authenticate</Button>
        <Button className="unavailable">Scan</Button>
        <Button className="unavailable" bsStyle="primary">Add</Button>
      </div>
    );
  }

  renderCounts() {
    const { activeFilters, totalCount, filteredCount } = this.props;

    return (
      <h5>
        {activeFilters && activeFilters.length > 0
          ? filteredCount + ' of '
          : null}
        {totalCount + ' Result'}
        {totalCount > 1 ? 's' : null}
      </h5>
    );
  }

  renderActiveFilters() {
    const { activeFilters } = this.props;

    if (activeFilters && activeFilters.length > 0) {
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
    } else {
      return null;
    }
  }

  render() {
    return (
      <Toolbar>
        {this.renderFilter()}
        {this.renderSort()}
        <Toolbar.RightContent>{this.renderActions()}</Toolbar.RightContent>
        <Toolbar.Results>
          {this.renderCounts()}
          {this.renderActiveFilters()}
        </Toolbar.Results>
      </Toolbar>
    );
  }
}

SourcesToolbar.propTypes = {
  totalCount: PropTypes.number,
  filteredCount: PropTypes.number,
  filterType: PropTypes.object,
  filterValue: PropTypes.any,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

function mapStateToProps(state, ownProps) {
  return {
    ...state.sourcesToolbar
  };
}

export default withRouter(connect(mapStateToProps)(SourcesToolbar));
