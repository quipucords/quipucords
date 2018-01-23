import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import { Button, Filter, Sort, Toolbar } from 'patternfly-react';

import { bindMethods } from '../../common/helpers';

import { ScanFilterFields, ScanSortFields } from './scanConstants';
import Store from '../../redux/store';
import { viewToolbarTypes as dispatchTypes } from '../../redux/constants/';

class ScansToolbar extends React.Component {
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
      this.selectFilterType(ScanFilterFields[0]);
    }

    if (!sortType) {
      this.updateCurrentSortType(ScanSortFields[0]);
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

    if (keyEvent.key === 'Enter' && filterValue && filterValue.length) {
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
    const { filterType } = this.props;

    return (
      <Filter>
        <Filter.TypeSelector
          filterTypes={ScanFilterFields}
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
            sortTypes={ScanSortFields}
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

  renderActions() {
    return (
      <div className="form-group">
        <Button
          disabled={this.props.runScansAvailable === false}
          onClick={this.props.onRunScans}
        >
          Scan Now
        </Button>
        <Button
          disabled={this.props.repeatScansAvailable === false}
          onClick={this.props.onRepeatScans}
        >
          Repeat Scan
        </Button>
        <Button
          disabled={this.props.downloadScansAvailable === false}
          onClick={this.props.onDownloadScans}
        >
          Download
        </Button>
      </div>
    );
  }

  renderCounts() {
    const { activeFilters, totalCount, filteredCount } = this.props;

    return (
      <h5>
        {activeFilters && activeFilters.length > 0
          ? `${filteredCount} of `
          : null}
        {totalCount + (totalCount > 1 ? ' Results' : ' Result')}
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

ScansToolbar.propTypes = {
  totalCount: PropTypes.number,
  filteredCount: PropTypes.number,
  filterType: PropTypes.object,
  filterValue: PropTypes.any,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool,
  runScansAvailable: PropTypes.bool,
  onRunScans: PropTypes.func,
  repeatScansAvailable: PropTypes.bool,
  onRepeatScans: PropTypes.func,
  downloadScansAvailable: PropTypes.bool,
  onDownloadScans: PropTypes.func
};

function mapStateToProps(state, ownProps) {
  return {
    ...state.scansToolbar
  };
}

export default connect(mapStateToProps)(ScansToolbar);
