import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import { Button, Filter, Icon, Sort, Toolbar } from 'patternfly-react';

import { bindMethods } from '../../common/helpers';
import Store from '../../redux/store';

import {
  CredentialFilterFields,
  CredentialSortFields
} from './crendentialConstants';
import { viewToolbarTypes } from '../../redux/constants';

class CredentialsToolbar extends React.Component {
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
      this.selectFilterType(CredentialFilterFields[0]);
    }

    if (!sortType) {
      this.updateCurrentSortType(CredentialSortFields[0]);
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
      type: viewToolbarTypes.ADD_FILTER,
      filter
    });
  }

  selectFilterType(filterType) {
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_TYPE,
      filterType
    });
  }

  filterValueSelected(newFilterValue) {
    const { filterType } = this.props;

    let filterValue = newFilterValue;
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_VALUE,
      filterValue
    });
    if (newFilterValue) {
      this.filterAdded(filterType, newFilterValue);
    }
  }

  updateCurrentValue(event) {
    let filterValue = event.target.value;
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_VALUE,
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
      type: viewToolbarTypes.REMOVE_FILTER,
      filter
    });
  }

  clearFilters() {
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS
    });
  }

  updateCurrentSortType(sortType) {
    Store.dispatch({
      type: viewToolbarTypes.SET_SORT_TYPE,
      sortType
    });
  }

  toggleCurrentSortDirection() {
    Store.dispatch({
      type: viewToolbarTypes.TOGGLE_SORT_ASCENDING
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
          filterTypes={CredentialFilterFields}
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
            sortTypes={CredentialSortFields}
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
        <Button bsStyle="primary" onClick={this.props.onAddCredential}>
          Add
        </Button>
        <Button
          disabled={this.props.deleteAvailable === false}
          onClick={this.props.onDelete}
        >
          Delete
        </Button>
        <Button onClick={this.props.onRefresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
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

CredentialsToolbar.propTypes = {
  totalCount: PropTypes.number,
  filteredCount: PropTypes.number,
  filterType: PropTypes.object,
  filterValue: PropTypes.any,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool,
  onAddCredential: PropTypes.func,
  deleteAvailable: PropTypes.bool,
  onDelete: PropTypes.func,
  onRefresh: PropTypes.func
};

function mapStateToProps(state, ownProps) {
  return {
    ...state.credentialsToolbar
  };
}

export default connect(mapStateToProps)(CredentialsToolbar);
