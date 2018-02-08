import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import Store from '../../redux/store';

import {
  Alert,
  Button,
  EmptyState,
  Icon,
  ListView,
  Modal
} from 'patternfly-react';

import { getSources } from '../../redux/actions/sourcesActions';
import {
  sourcesTypes,
  toastNotificationTypes,
  confirmationModalTypes,
  viewTypes
} from '../../redux/constants';
import { bindMethods } from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import SourcesEmptyState from './sourcesEmptyState';
import { SourceListItem } from './sourceListItem';
import { CreateScanDialog } from './createScanDialog';
import { AddSourceWizard } from './addSourceWizard';
import { SourceFilterFields, SourceSortFields } from './sourceConstants';

class Sources extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'importSources',
      'scanSource',
      'scanSources',
      'itemSelectChange',
      'editSource',
      'deleteSource',
      'hideScanDialog',
      'createScan',
      'refresh',
      'showAddSourceWizard',
      'quitAddSourceWizard'
    ]);

    this.state = {
      filteredItems: [],
      selectedItems: [],
      scanDialogShown: false,
      multiSourceScan: false,
      currentScanSource: null,
      addSourceWizardShown: false
    };
  }

  componentDidMount() {
    this.props.getSources();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.sources && nextProps.sources !== this.props.sources) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.sources.forEach(source => {
        source.selected = false;
      });

      // TODO: Remove once we get real failed host data
      nextProps.sources.forEach(source => {
        let failedCount = Math.floor(Math.random() * 10);
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
        return this.matchString(item.name, filter.value);
      case 'sourceType':
        return item.source_type === filter.value.id;
      case 'hosts':
        return (
          item.hosts &&
          item.hosts.find(host => {
            return this.matchString(host, filter.value);
          })
        );
      case 'status':
        return (
          item.connection_scan &&
          item.connection_scan.status === filter.value.id
        );
      case 'credentials':
        return (
          item.credentials &&
          item.credentials.find(credential => {
            return this.matchString(credential.name, filter.value);
          })
        );
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
        case 'status':
          compValue = item1.source_type.localeCompare(item2.source_type);
          break;
        case 'credentialsCount':
          compValue = item1.credentials.length - item2.credentials.length;
          break;
        case 'hostCount':
          compValue =
            item1.hosts.length +
            item1.failed_hosts.length -
            (item2.hosts.length + item2.failed_hosts.length);
          break;
        case 'successHostCount':
          compValue = item1.hosts.length - item2.hosts.length;
          break;
        case 'failedHostCount':
          compValue = item1.failed_hosts.length - item2.failed_hosts.length;
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

  showAddSourceWizard() {
    this.setState({ addSourceWizardShown: true });
  }

  quitAddSourceWizard() {
    let onConfirm = () => {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });

      this.setState({ addSourceWizardShown: false });
    };

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Cancel Add Source',
      heading: 'Are you sure you want to exit this wizard?',
      body: 'Exiting this wizard will cancel adding the source.',
      cancelButtonText: 'No',
      confirmButtonText: 'Yes',
      onConfirm: onConfirm
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

  scanSource(source) {
    this.setState({
      scanDialogShown: true,
      multiSourceScan: false,
      currentScanSource: source
    });
  }

  scanSources() {
    this.setState({ scanDialogShown: true, multiSourceScan: true });
  }

  hideScanDialog() {
    this.setState({ scanDialogShown: false });
  }

  itemSelectChange(item) {
    const { filteredItems } = this.state;

    item.selected = !item.selected;
    let selectedItems = filteredItems.filter(item => {
      return item.selected === true;
    });

    this.setState({ selectedItems: selectedItems });

    Store.dispatch({
      type: sourcesTypes.SOURCES_SELECTED,
      selectedSources: selectedItems
    });
  }

  editSource(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Editing sources is not yet implemented'
    });
  }

  doDeleteSource(item) {
    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Deleting sources is not yet implemented'
    });
  }

  deleteSource(item) {
    let heading = (
      <span>
        Are you sure you want to delete the source <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteSource(item);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  createScan(scanName, sources) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: scanName,
      message: 'Scanning sources is not yet implemented'
    });
    this.hideScanDialog();
  }

  refresh() {
    this.props.getSources();
  }

  renderActions() {
    const { selectedItems } = this.state;

    return (
      <div className="form-group">
        <Button bsStyle="primary" onClick={this.showAddSourceWizard}>
          Add
        </Button>
        <Button
          disabled={!selectedItems || selectedItems.length === 0}
          onClick={this.scanSources}
        >
          Scan
        </Button>
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
          <SourceListItem
            item={item}
            key={index}
            onItemSelectChange={this.itemSelectChange}
            onEdit={this.editSource}
            onDelete={this.deleteSource}
            onScan={this.scanSource}
          />
        ))}
      </ListView>
    );
  }

  render() {
    const {
      pending,
      error,
      errorMessage,
      sources,
      filterType,
      filterValue,
      activeFilters,
      sortType,
      sortAscending
    } = this.props;
    const {
      filteredItems,
      selectedItems,
      scanDialogShown,
      multiSourceScan,
      currentScanSource,
      addSourceWizardShown
    } = this.state;

    if (pending) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (sources && sources.length) {
      this.sortSources(filteredItems);

      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.SOURCES_VIEW}
              totalCount={sources.length}
              filteredCount={filteredItems.length}
              filterFields={SourceFilterFields}
              sortFields={SourceSortFields}
              actions={this.renderActions()}
              itemsType="Source"
              itemsTypePlural="Sources"
              filterType={filterType}
              filterValue={filterValue}
              activeFilters={activeFilters}
              sortType={sortType}
              sortAscending={sortAscending}
            />
            <div className="quipucords-list-container">
              {this.renderList(filteredItems)}
            </div>
            <AddSourceWizard
              show={addSourceWizardShown}
              onCancel={this.quitAddSourceWizard}
            />
            <CreateScanDialog
              show={scanDialogShown}
              sources={multiSourceScan ? selectedItems : [currentScanSource]}
              onCancel={this.hideScanDialog}
              onScan={this.createScan}
            />
          </div>
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState
          onAddSource={this.showAddSourceWizard}
          onImportSources={this.importSources}
        />
        <AddSourceWizard
          show={addSourceWizardShown}
          onCancel={this.quitAddSourceWizard}
        />
      </React.Fragment>
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  sources: PropTypes.array,

  filterType: PropTypes.object,
  filterValue: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: () => dispatch(getSources())
});

const mapStateToProps = function(state) {
  return Object.assign(
    {},
    state.sources.view,
    state.sources.persist,
    state.toolbars[viewTypes.SOURCES_VIEW]
  );
};

export default connect(mapStateToProps, mapDispatchToProps)(Sources);
