import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Grid,
  EmptyState,
  Row,
  ListView,
  Modal
} from 'patternfly-react';

import { getSources } from '../../redux/actions/sourcesActions';

import SourcesToolbar from './sourcesToolbar';
import SourcesEmptyState from './sourcesEmptyState';
import { SourceListItem } from './sourceListItem';
import Store from '../../redux/store';
import { toastNotificationTypes } from '../../redux/constants';
import { bindMethods } from '../../common/helpers';

class Sources extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'addSource',
      'importSources',
      'authenticateSources',
      'scanSources',
      'itemSelectChange'
    ]);
    this.state = {
      filteredItems: [],
      selectedItems: []
    };
  }

  componentDidMount() {
    this.props.getSources();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.sources !== this.props.sources) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.sources.forEach(source => {
        source.selected = false;
      });

      // TODO: Remove once we get real failed host data
      let failedCount = Math.floor(Math.random() * 10);
      nextProps.sources.forEach(source => {
        source.selected = false;
        source.failed_hosts = [];
        for (let i = 0; i < failedCount; i++) {
          source.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      let filteredItems = this.filterSources(
        nextProps.sources,
        nextProps.activeFilters
      );

      this.setState({ filteredItems: filteredItems, selectedItems: [] });
    } else if (nextProps.activeFilters !== this.props.activeFilters) {
      let filteredItems = this.filterSources(
        nextProps.sources,
        nextProps.activeFilters
      );
      this.setState({ filteredItems: filteredItems });
    }
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return item.name.match(re) !== null;
      case 'sourceType':
        return item.source_type === filter.value.id;
      default:
        return true;
    }
  }

  matchesFilters(item, filters) {
    let matches = true;

    filters.forEach(filter => {
      if (!this.matchesFilter(item, filter)) {
        matches = false;
        return false;
      }
    });
    return matches;
  }

  filterSources(sources, filters) {
    if (!filters || filters.length === 0) {
      return sources;
    }

    return sources.filter(item => {
      return this.matchesFilters(item, filters);
    });
  }

  sortSources(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.name.localeCompare(item2.name);
          break;
        case 'sourceType':
          compValue = item1.source_type.localeCompare(item2.source_type);
          break;
        case 'hostCount':
          compValue = item1.hosts.length - item2.hosts.length;
          break;
        default:
          compValue = 0;
      }

      if (!sortAscending) {
        compValue = compValue * -1;
      }

      return compValue;
    });
  }

  addSource() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Importing sources is not yet implemented'
    });
  }

  importSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Adding sources is not yet implemented'
    });
  }

  authenticateSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Authenticating sources is not yet implemented'
    });
  }

  scanSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Scanning sources is not yet implemented'
    });
  }

  itemSelectChange(item) {
    const { filteredItems } = this.state;

    item.selected = !item.selected;
    let selectedItems = filteredItems.filter(item => {
      return item.selected === true;
    });

    this.setState({ selectedItems: selectedItems });
  }

  renderList(items) {
    return (
      <Row>
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <SourceListItem
              item={item}
              key={index}
              onItemSelectChange={this.itemSelectChange}
            />
          ))}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, sources } = this.props;
    const { filteredItems, selectedItems } = this.state;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
      return (
        <EmptyState>
          <Alert type="danger">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (sources && sources.length) {
      this.sortSources(filteredItems);

      return [
        <SourcesToolbar
          totalCount={sources.length}
          filteredCount={filteredItems.length}
          key={1}
          onAddSource={this.addSource}
          authenticateAvailable={selectedItems && selectedItems.length > 0}
          onAuthenticate={this.authenticateSources}
          scanAvailable={selectedItems && selectedItems.length > 0}
          onScan={this.scanSources}
        />,
        <Grid fluid key={2}>
          {this.renderList(filteredItems)}
        </Grid>
      ];
    }
    return (
      <SourcesEmptyState
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  sources: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Sources.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: () => dispatch(getSources())
});

function mapStateToProps(state) {
  return {
    loading: state.sources.loading,
    sources: state.sources.data,
    loadError: state.sources.error,
    errorMessage: state.sources.errorMessage,
    activeFilters: state.sourcesToolbar.activeFilters,
    sortType: state.sourcesToolbar.sortType,
    sortAscending: state.sourcesToolbar.sortAscending
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Sources);
