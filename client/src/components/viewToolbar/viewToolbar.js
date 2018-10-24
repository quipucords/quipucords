import React from 'react';
import PropTypes from 'prop-types';
import { Button, Filter, Sort, Toolbar } from 'patternfly-react';
import _ from 'lodash';
import Store from '../../redux/store';
import { viewToolbarTypes } from '../../redux/constants';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import RefreshTimeButton from '../refreshTimeButton/refreshTimeButton';
import helpers from '../../common/helpers';

class ViewToolbar extends React.Component {
  componentDidMount() {
    const { filterType, sortType, filterFields, sortFields } = this.props;

    if (!filterType) {
      this.onSelectFilterType(filterFields[0]);
    }

    if (!sortType) {
      this.onUpdateCurrentSortType(sortFields[0]);
    }
  }

  onFilterAdded = (field, value) => {
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

    const filter = { field, value, label: filterText };
    Store.dispatch({
      type: viewToolbarTypes.ADD_FILTER,
      viewType,
      filter
    });
  };

  onSelectFilterType = filterType => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_TYPE,
      viewType,
      filterType
    });
  };

  onFilterValueSelected = newFilterValue => {
    const { filterType, viewType } = this.props;

    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_VALUE,
      viewType,
      filterValue: newFilterValue
    });

    if (newFilterValue) {
      this.onFilterAdded(filterType, newFilterValue);
    }
  };

  onUpdateCurrentValue = event => {
    const { viewType } = this.props;
    const filterValue = event.target.value;

    Store.dispatch({
      type: viewToolbarTypes.SET_FILTER_VALUE,
      viewType,
      filterValue
    });
  };

  onValueKeyPress = keyEvent => {
    const { filterType, filterValue } = this.props;

    if (keyEvent.key === 'Enter' && filterValue && filterValue.length) {
      this.onFilterAdded(filterType, filterValue);
      keyEvent.stopPropagation();
      keyEvent.preventDefault();
    }
  };

  onRemoveFilter = filter => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.REMOVE_FILTER,
      viewType,
      filter
    });
  };

  onClearFilters = () => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType
    });
  };

  onUpdateCurrentSortType = sortType => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.SET_SORT_TYPE,
      viewType,
      sortType
    });
  };

  onToggleCurrentSortDirection = () => {
    const { viewType } = this.props;
    Store.dispatch({
      type: viewToolbarTypes.TOGGLE_SORT_ASCENDING,
      viewType
    });
  };

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
          onFilterValueSelected={this.onFilterValueSelected}
        />
      );
    }

    return (
      <input
        className="form-control"
        type={filterType.filterType}
        value={filterValue}
        placeholder={filterType.placeholder}
        onChange={e => this.onUpdateCurrentValue(e)}
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
            onFilterTypeSelected={this.onSelectFilterType}
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
            onSortTypeSelected={this.onUpdateCurrentSortType}
          />
          <SimpleTooltip id="sortTip" tooltip={`Sort by ${sortType.title}`}>
            <Sort.DirectionSelector
              isNumeric={sortType.isNumeric}
              isAscending={sortAscending}
              onClick={() => this.onToggleCurrentSortDirection()}
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
          {activeFilters.map(item => (
            <Filter.Item key={item.label} onRemove={this.onRemoveFilter} filterData={item}>
              {item.label}
            </Filter.Item>
          ))}
        </Filter.List>,
        <Button bsStyle="link" key="clear" onClick={this.onClearFilters}>
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
  viewType: null,
  totalCount: 0,
  selectedCount: 0,
  filterFields: [],
  sortFields: [],
  onRefresh: helpers.noop,
  lastRefresh: 0,
  actions: null,
  itemsType: '',
  itemsTypePlural: '',
  filterType: {},
  filterValue: '',
  activeFilters: [],
  sortType: {},
  sortAscending: true
};

export { ViewToolbar as default, ViewToolbar };
