import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Button,
  EmptyState,
  Icon,
  ListView,
  Modal
} from 'patternfly-react';

import { bindMethods } from '../../common/helpers';
import Store from '../../redux/store';
import {
  toastNotificationTypes,
  viewToolbarTypes
} from '../../redux/constants';
import { getScans } from '../../redux/actions/scansActions';

import ViewToolbar from '../viewToolbar/viewToolbar';

import SourcesEmptyState from '../sources/sourcesEmptyState';
import { ScanListItem } from './scanListItem';
import { ScanFilterFields, ScanSortFields } from './scanConstants';

class Scans extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'downloadSummaryReport',
      'downloadDetailedReport',
      'pauseScan',
      'cancelScan',
      'startScan',
      'resumeScan',
      'addSource',
      'importSources',
      'refresh'
    ]);
    this.state = {
      filteredItems: []
    };
  }

  componentDidMount() {
    this.props.getScans({ scan_type: 'inspect' });
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.scans !== this.props.scans) {
      nextProps.scans.forEach(scan => {
        scan.systems_scanned = Math.abs(scan.systems_scanned) % 100;
        scan.systems_failed = Math.abs(scan.systems_failed) % 100;
        scan.scans_count = Math.floor(Math.random() * 10);

        // TODO: Get real hosts or wait until expansion?
        scan.hosts = [];
        for (let i = 0; i < scan.systems_scanned; i++) {
          scan.hosts.push('host' + (i + 1));
        }
        scan.failed_hosts = [];
        for (let i = 0; i < scan.systems_failed; i++) {
          scan.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      let filteredItems = this.filterScans(
        nextProps.scans,
        nextProps.activeFilters
      );

      this.setState({ filteredItems: filteredItems, selectedItems: [] });
    } else if (nextProps.activeFilters !== this.props.activeFilters) {
      let filteredItems = this.filterScans(
        nextProps.scans,
        nextProps.activeFilters
      );
      this.setState({ filteredItems: filteredItems });
    }
  }

  matchString(value, match) {
    if (!value) {
      return false;
    }

    if (!match) {
      return true;
    }

    return value.toLowerCase().includes(match.toLowerCase());
  }

  matchesFilter(item, filter) {
    switch (filter.field.id) {
      case 'name':
        return this.matchString(item.id, filter.value); // Using ID for now until we get a name
      case 'source':
        return (
          item.sources &&
          item.sources.find(source => {
            return this.matchString(source.name, filter.value);
          })
        );
      case 'status':
        return item.status === filter.value.id;
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

  filterScans(scans, filters) {
    return scans.filter(item => {
      return this.matchesFilters(item, filters);
    });
  }

  sortScans(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.id - item2.id; // Using ID for now until we get a name
          break;
        case 'status':
          compValue = item1.status.localeCompare(item2.status);
          break;
        case 'time':
          compValue = item1.status.localeCompare(item2.status);
          break;
        case 'hostCount':
          compValue = item1.systems_count - item2.systems_count;
          break;
        case 'successfulHosts':
          compValue = item1.systems_scanned - item2.systems_scanned;
          break;
        case 'failedHosts':
          compValue = item1.systems_failed - item2.systems_failed;
          break;
        case 'sourceCount':
          compValue = item1.sources.length - item2.sources.length;
          break;
        case 'scansCount':
          compValue = item1.scans_count - item2.scans_count;
          break;
        default:
          compValue = 0;
      }

      // Secondary sort by time
      if (compValue === 0) {
        compValue = item2.last_run - item1.last_run;
      }

      // Tertiary sort by status
      if (compValue === 0) {
        compValue = item1.status.localeCompare(item2.status);
      }

      if (!sortAscending) {
        compValue = compValue * -1;
      }

      return compValue;
    });
  }

  downloadSummaryReport() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading summary reports is not yet implemented'
    });
  }

  downloadDetailedReport() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading summary reports is not yet implemented'
    });
  }

  pauseScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Pausing scans is not yet implemented'
    });
  }

  cancelScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Cancelling scans is not yet implemented'
    });
  }

  startScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Starting scans is not yet implemented'
    });
  }

  resumeScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.id,
      message: 'Resuming scans is not yet implemented'
    });
  }

  addSource() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Adding sources is not yet implemented'
    });
  }

  importSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Importing sources is not yet implemented'
    });
  }

  refresh() {
    this.props.getScans({ scan_type: 'inspect' });
  }

  renderActions() {
    return (
      <div className="form-group">
        <Button onClick={this.refresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
        </Button>
      </div>
    );
  }

  renderList(items) {
    return (
      <ListView className="quipicords-list-view">
        {items.map((item, index) => (
          <ScanListItem
            item={item}
            key={index}
            onSummaryDownload={this.downloadSummaryReport}
            onDetailedDownload={this.downloadDetailedReport}
            onPause={this.pauseScan}
            onCancel={this.cancelScan}
            onStart={this.startScan}
            onResume={this.resumeScan}
          />
        ))}
      </ListView>
    );
  }

  render() {
    const {
      loading,
      loadError,
      errorMessage,
      scans,
      filterType,
      filterValue,
      activeFilters,
      sortType,
      sortAscending
    } = this.props;
    const { filteredItems } = this.state;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading scans...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving scans: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }
    if (scans && scans.length) {
      this.sortScans(filteredItems);

      return (
        <div className="quipucords-view-container">
          <ViewToolbar
            viewType={viewToolbarTypes.SCANS_VIEW}
            totalCount={scans.length}
            filteredCount={filteredItems.length}
            filterFields={ScanFilterFields}
            sortFields={ScanSortFields}
            actions={this.renderActions()}
            itemsType="Scan"
            itemsTypePlural="Scans"
            filterType={filterType}
            filterValue={filterValue}
            activeFilters={activeFilters}
            sortType={sortType}
            sortAscending={sortAscending}
          />
          <div className="quipucords-list-container">
            {this.renderList(filteredItems)}
          </div>
        </div>
      );
    }
    return (
      <SourcesEmptyState
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />
    );
  }
}

Scans.propTypes = {
  getScans: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  scans: PropTypes.array,
  filterType: PropTypes.object,
  filterValue: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Scans.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScans: () => dispatch(getScans())
});

function mapStateToProps(state) {
  return {
    loading: state.scans.loading,
    scans: state.scans.data,
    loadError: state.scans.error,
    errorMessage: state.scans.errorMessage,
    filterType: state.scansToolbar.filterType,
    filterValue: state.scansToolbar.filterValue,
    activeFilters: state.scansToolbar.activeFilters,
    sortType: state.scansToolbar.sortType,
    sortAscending: state.scansToolbar.sortAscending
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Scans);
